const OPTION_LABELS = ["イ", "ロ", "ハ", "ニ"];
const EXAM_MINUTES = 120;
const ASSET_VERSION = "20261018-2";

const state = {
  catalog: [],
  examId: "2026-upper",
  loadedExamId: "",
  assetBase: "output",
  allQuestions: [],
  questions: [],
  mode: "all",
  current: 0,
  answers: {},
  mistakes: {},
  hints: {},
  reviewingResult: false,
  remaining: EXAM_MINUTES * 60,
  timerId: null,
  submitted: false
};

const $ = (selector) => document.querySelector(selector);
const startScreen = $("#start-screen");
const figScreen = $("#fig-screen");
const examScreen = $("#exam-screen");
const resultScreen = $("#result-screen");
const figState = { cards: [], current: 0, revealed: false, frontLabel: "カード", backLabel: "答え" };

function showScreen(screen) {
  [startScreen, figScreen, examScreen, resultScreen].forEach((item) => item.classList.add("hidden"));
  screen.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadQuestions() {
  if (state.loadedExamId === state.examId && state.allQuestions.length) return;
  const selectedExam = state.catalog.find((exam) => exam.id === state.examId);
  const response = await fetch(selectedExam.data);
  if (!response.ok) throw new Error("問題データを読み込めませんでした");
  state.allQuestions = await response.json();
  state.loadedExamId = state.examId;
  state.assetBase = selectedExam.data.slice(0, selectedExam.data.lastIndexOf("/"));
}

async function loadCatalog() {
  if (state.catalog.length) return;
  const response = await fetch("output/exams.json?v=20261018-2");
  if (!response.ok) throw new Error("試験年度データを読み込めませんでした");
  state.catalog = await response.json();
  renderExamChoices();
}

async function loadFigures() {
  if (figState.cards.length) return;
  const response = await fetch("card.csv");
  if (!response.ok) throw new Error("暗記カードデータを読み込めませんでした");
  const text = await response.text();
  const lines = text.split(/\r?\n/);
  const headers = lines.shift().split(",").map((value) => value.trim());
  figState.frontLabel = headers[0] || "カード";
  figState.backLabel = headers[1] || "答え";
  figState.cards = lines.map((line) => {
    const comma = line.indexOf(",");
    if (comma < 0) return null;
    return { symbol: line.slice(0, comma).trim(), meaning: line.slice(comma + 1).trim().replace(/,$/, "") };
  }).filter((card) => card && card.symbol && card.meaning);
}

function renderFigureCard() {
  const card = figState.cards[figState.current];
  if (!card) return;
  $("#fig-progress").textContent = `${figState.current + 1} / ${figState.cards.length}`;
  $("#fig-card-label").textContent = figState.frontLabel;
  $("#fig-symbol").textContent = card.symbol;
  $("#fig-meaning").textContent = figState.revealed
    ? `${figState.backLabel}: ${card.meaning}`
    : `タップして${figState.backLabel}を表示`;
  $("#fig-meaning").classList.toggle("visible", figState.revealed);
  $("#fig-card").setAttribute("aria-expanded", figState.revealed ? "true" : "false");
  $("#fig-reveal-button").textContent = figState.revealed ? `${figState.backLabel}を隠す` : `${figState.backLabel}を見る`;
  $("#fig-prev-button").disabled = figState.current === 0;
  $("#fig-next-button").disabled = figState.current === figState.cards.length - 1;
}

async function openFigureCards() {
  try {
    await loadFigures();
    figState.current = 0;
    figState.revealed = false;
    renderFigureCard();
    showScreen(figScreen);
  } catch (error) {
    alert(`${error.message}\nローカルサーバー経由で開いてください。`);
  }
}

function renderExamChoices() {
  const container = $("#exam-sets");
  container.innerHTML = "";
  state.catalog.forEach((exam) => {
    const button = document.createElement("button");
    button.className = `exam-button ${exam.id === state.examId ? "selected" : ""}`;
    button.textContent = exam.label;
    button.addEventListener("click", () => {
      state.examId = exam.id;
      const selected = state.catalog.find((item) => item.id === state.examId);
      $("#selected-exam-label").textContent = selected.label;
      renderExamChoices();
    });
    container.appendChild(button);
  });
}

function renderQuestion() {
  const question = state.questions[state.current];
  const number = question.number;
  const position = state.current + 1;
  $("#progress-text").textContent = `問題 ${position} / ${state.questions.length}`;
  $("#answered-text").textContent = `回答済み ${Object.keys(state.answers).length}問`;
  $("#nav-count").textContent = `${Object.keys(state.answers).length} / ${state.questions.length}`;
  $("#progress-bar").style.width = `${(position / state.questions.length) * 100}%`;
  $("#section-label").textContent = number <= 30 ? `問題${number}・一般問題` : `問題${number}・配線図`;
  examScreen.classList.toggle("wiring-layout", state.mode === "wiring");
  const diagramLink = $("#diagram-link");
  diagramLink.classList.toggle("hidden", state.mode !== "wiring");
  diagramLink.href = `${state.assetBase}/diagram.png?v=${ASSET_VERSION}`;
  $("#diagram-panel").classList.toggle("hidden", state.mode !== "wiring");
  $("#diagram-image").src = diagramLink.href;
  $("#diagram-panel-link").href = diagramLink.href;
  $(".question-card").classList.toggle("wrong-state", Boolean(state.mistakes[number] && state.answers[number] !== question.answer));
  // questions.json lives in output/, so resolve its image path from the site root.
  $("#question-image").src = `${state.assetBase}/${question.question_image}?v=${ASSET_VERSION}`;
  $("#question-image").alt = `第二種電気工事士 問題${number}の問題文`;
  $("#answer-image").src = `${state.assetBase}/${question.answer_image}?v=${ASSET_VERSION}`;
  $("#answer-image").alt = `第二種電気工事士 問題${number}の選択肢`;
  $("#prev-button").disabled = state.current === 0;
  $("#next-button").innerHTML = state.current === state.questions.length - 1 ? "解答を提出する <span>✓</span>" : "次の問題 <span>→</span>";
  $("#return-result-button").classList.toggle("hidden", !state.reviewingResult);

  const options = $("#answer-options");
  options.innerHTML = "";
  const feedback = $("#answer-feedback");
  const wrongNow = state.mistakes[number] && state.answers[number] !== question.answer;
  const explanationVisible = Boolean(state.hints[number]);
  feedback.textContent = wrongNow
    ? "不正解です。問題文を確認して、正解を選ぶまで次の問題には進めません。"
    : "";
  feedback.className = feedback.textContent ? "answer-feedback visible" : "answer-feedback";
  const hintButton = $("#hint-button");
  hintButton.textContent = explanationVisible ? "解説を隠す" : "ヒントを見る";
  hintButton.setAttribute("aria-expanded", explanationVisible ? "true" : "false");
  const explanationPanel = $("#explanation-panel");
  explanationPanel.className = explanationVisible ? "explanation-panel visible" : "explanation-panel";
  $("#explanation-text").textContent = question.explanation || "この問題の解説は準備中です。正答と問題文を確認してください。";
  OPTION_LABELS.forEach((label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "answer-option";
    button.textContent = label;
    button.disabled = state.reviewingResult;
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", state.answers[number] === label ? "true" : "false");
    if (state.answers[number] === label) button.classList.add("selected");
    if (state.mistakes[number] && state.answers[number] === label && label !== question.answer) button.classList.add("wrong-selected");
    button.addEventListener("click", () => {
      state.answers[number] = label;
      if (label !== question.answer) {
        state.mistakes[number] = true;
        state.hints[number] = true;
        renderQuestion();
        $("#question-image").scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
      if (state.current === state.questions.length - 1) submitExam();
      else { state.current += 1; renderQuestion(); }
    });
    options.appendChild(button);
  });
  renderQuestionGrid();
}

function renderQuestionGrid() {
  const grid = $("#question-grid");
  grid.innerHTML = "";
  state.questions.forEach((question, index) => {
    const button = document.createElement("button");
    button.className = "question-number";
    button.textContent = question.number;
    button.title = `問題${question.number}へ移動`;
    if (index === state.current) button.classList.add("current");
    if (state.answers[question.number]) button.classList.add("answered");
    button.addEventListener("click", () => { state.current = index; renderQuestion(); });
    grid.appendChild(button);
  });
}

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const rest = (seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${rest}`;
}

function startTimer() {
  clearInterval(state.timerId);
  $("#timer").textContent = formatTime(state.remaining);
  state.timerId = setInterval(() => {
    state.remaining -= 1;
    $("#timer").textContent = formatTime(Math.max(0, state.remaining));
    if (state.remaining <= 300) $(".timer").style.color = "var(--coral)";
    if (state.remaining <= 0) submitExam(true);
  }, 1000);
}

function submitExam(timeUp = false) {
  if (state.submitted) return;
  state.submitted = true;
  clearInterval(state.timerId);
  const correct = state.questions.filter((q) => !state.mistakes[q.number] && state.answers[q.number] === q.answer).length;
  const unanswered = state.questions.filter((q) => !state.answers[q.number]).length;
  const mistakeQuestions = state.questions.filter((q) => state.mistakes[q.number]).length;
  const wrong = state.questions.length - correct - unanswered;
  const totalQuestions = state.questions.length;
  const accuracy = totalQuestions ? Math.round((correct / totalQuestions) * 100) : 0;
  $("#result-title").textContent = accuracy >= 60 ? "合格ライン到達です。" : "ここから伸ばしていきましょう。";
  $("#result-summary").textContent = timeUp ? "制限時間になりました。解答を採点しました。" : "解答を採点しました。間違えた問題を復習してみましょう。";
  $("#score-value").textContent = accuracy;
  $("#score-detail").textContent = `${correct} / ${totalQuestions}問`;
  $("#correct-count").textContent = `${correct}問`;
  $("#wrong-count").textContent = `${wrong}問`;
  $("#unanswered-count").textContent = `${unanswered}問`;
  $("#mistake-count").textContent = `${mistakeQuestions}問`;
  $("#score-ring").style.background = `conic-gradient(var(--blue) ${accuracy * 3.6}deg, #e8edf5 ${accuracy * 3.6}deg)`;
  const list = $("#review-list");
  list.innerHTML = "";
  state.questions.forEach((q, index) => {
    const selected = state.answers[q.number] || "未回答";
    const hasMistake = Boolean(state.mistakes[q.number]);
    const isCorrect = !hasMistake && selected === q.answer;
    const isUnanswered = !state.answers[q.number];
    const item = document.createElement("div");
    item.className = `review-item ${isCorrect ? "correct" : "incorrect"}`;
    const historyLabel = hasMistake ? "誤答" : "正解";
    const explanation = q.explanation ? `<span class="review-explanation">正答の理由：${q.explanation}</span>` : "";
    const badge = isUnanswered ? "未回答" : historyLabel;
    item.innerHTML = `<span class="review-q">問${q.number}</span><span class="review-answer">あなたの答え <strong>${selected}</strong> ／ 正答 <strong>${q.answer}</strong>${explanation}</span><span class="review-badge">${badge}</span>`;
    item.addEventListener("click", () => { state.current = index; state.reviewingResult = true; showScreen(examScreen); renderQuestion(); });
    list.appendChild(item);
  });
  showScreen(resultScreen);
}

async function startExam() {
  $("#start-button").disabled = true;
  try {
    await loadCatalog();
    await loadQuestions();
    state.questions = state.mode === "general"
      ? state.allQuestions.filter((question) => question.number <= 30)
      : state.mode === "wiring"
        ? state.allQuestions.filter((question) => question.number >= 31)
        : [...state.allQuestions];
    state.current = 0;
    state.answers = {};
    state.mistakes = {};
    state.hints = {};
    state.reviewingResult = false;
    state.remaining = EXAM_MINUTES * 60;
    state.submitted = false;
    showScreen(examScreen);
    renderQuestion();
    startTimer();
  } catch (error) {
    alert(`${error.message}\nローカルサーバー経由で開いてください。`);
  } finally {
    $("#start-button").disabled = false;
  }
}

document.querySelectorAll(".mode-button").forEach((button) => {
  button.addEventListener("click", () => {
    state.mode = button.dataset.mode;
    document.querySelectorAll(".mode-button").forEach((item) => item.classList.remove("selected"));
    button.classList.add("selected");
  });
});
$("#start-button").addEventListener("click", startExam);
$("#fig-button").addEventListener("click", openFigureCards);
$("#home-button").addEventListener("click", () => {
  clearInterval(state.timerId);
  state.reviewingResult = false;
  showScreen(startScreen);
});
$("#hint-button").addEventListener("click", () => {
  const question = state.questions[state.current];
  if (!question) return;
  state.hints[question.number] = !state.hints[question.number];
  renderQuestion();
});
$("#prev-button").addEventListener("click", () => { if (state.current > 0) { state.current -= 1; renderQuestion(); } });
$("#next-button").addEventListener("click", () => { if (state.current === state.questions.length - 1) submitExam(); else { state.current += 1; renderQuestion(); } });
$("#return-result-button").addEventListener("click", () => { state.reviewingResult = false; showScreen(resultScreen); });
$("#restart-button").addEventListener("click", () => { showScreen(startScreen); $(".timer").style.color = "var(--blue-deep)"; });
$("#fig-card").addEventListener("click", () => {
  if (figState.revealed) {
    figState.current = (figState.current + 1) % figState.cards.length;
    figState.revealed = false;
  } else {
    figState.revealed = true;
  }
  renderFigureCard();
});
$("#fig-reveal-button").addEventListener("click", () => { figState.revealed = !figState.revealed; renderFigureCard(); });
$("#fig-prev-button").addEventListener("click", () => { if (figState.current > 0) { figState.current -= 1; figState.revealed = false; renderFigureCard(); } });
$("#fig-next-button").addEventListener("click", () => { if (figState.current < figState.cards.length - 1) { figState.current += 1; figState.revealed = false; renderFigureCard(); } });
$("#fig-shuffle-button").addEventListener("click", () => {
  for (let i = figState.cards.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [figState.cards[i], figState.cards[j]] = [figState.cards[j], figState.cards[i]];
  }
  figState.current = 0;
  figState.revealed = false;
  renderFigureCard();
});
$("#fig-home-button").addEventListener("click", () => showScreen(startScreen));
loadCatalog().catch((error) => console.warn(error.message));
