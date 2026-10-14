const OPTION_LABELS = ["イ", "ロ", "ハ", "ニ"];
const EXAM_MINUTES = 120;

const state = {
  questions: [],
  current: 0,
  answers: {},
  remaining: EXAM_MINUTES * 60,
  timerId: null,
  submitted: false
};

const $ = (selector) => document.querySelector(selector);
const startScreen = $("#start-screen");
const examScreen = $("#exam-screen");
const resultScreen = $("#result-screen");

function showScreen(screen) {
  [startScreen, examScreen, resultScreen].forEach((item) => item.classList.add("hidden"));
  screen.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadQuestions() {
  const response = await fetch("output/questions.json");
  if (!response.ok) throw new Error("問題データを読み込めませんでした");
  state.questions = await response.json();
}

function renderQuestion() {
  const question = state.questions[state.current];
  const number = question.number;
  $("#progress-text").textContent = `問題 ${number} / ${state.questions.length}`;
  $("#answered-text").textContent = `回答済み ${Object.keys(state.answers).length}問`;
  $("#nav-count").textContent = `${Object.keys(state.answers).length} / ${state.questions.length}`;
  $("#progress-bar").style.width = `${(number / state.questions.length) * 100}%`;
  $("#section-label").textContent = number <= 30 ? `問題${number}・一般問題` : `問題${number}・配線図`;
  // questions.json lives in output/, so resolve its image path from the site root.
  $("#question-image").src = `output/${question.image}`;
  $("#question-image").alt = `第二種電気工事士 問題${number}`;
  $("#prev-button").disabled = state.current === 0;
  $("#next-button").innerHTML = state.current === state.questions.length - 1 ? "解答を提出する <span>✓</span>" : "次の問題 <span>→</span>";

  const options = $("#answer-options");
  options.innerHTML = "";
  OPTION_LABELS.forEach((label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "answer-option";
    button.textContent = label;
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", state.answers[number] === label ? "true" : "false");
    if (state.answers[number] === label) button.classList.add("selected");
    button.addEventListener("click", () => {
      state.answers[number] = label;
      renderQuestion();
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
  const correct = state.questions.filter((q) => state.answers[q.number] === q.answer).length;
  const unanswered = state.questions.filter((q) => !state.answers[q.number]).length;
  const score = correct * 2;
  $("#result-title").textContent = score >= 60 ? "合格ライン到達です。" : "ここから伸ばしていきましょう。";
  $("#result-summary").textContent = timeUp ? "制限時間になりました。解答を採点しました。" : "解答を採点しました。間違えた問題を復習してみましょう。";
  $("#score-value").textContent = score;
  $("#correct-count").textContent = `${correct}問`;
  $("#wrong-count").textContent = `${state.questions.length - correct - unanswered}問`;
  $("#unanswered-count").textContent = `${unanswered}問`;
  $("#score-ring").style.background = `conic-gradient(var(--blue) ${score * 3.6}deg, #e8edf5 ${score * 3.6}deg)`;
  const list = $("#review-list");
  list.innerHTML = "";
  state.questions.forEach((q, index) => {
    const selected = state.answers[q.number] || "未回答";
    const isCorrect = selected === q.answer;
    const item = document.createElement("div");
    item.className = `review-item ${isCorrect ? "correct" : "incorrect"}`;
    item.innerHTML = `<span class="review-q">問${q.number}</span><span class="review-answer">あなたの答え <strong>${selected}</strong> ／ 正答 <strong>${q.answer}</strong></span><span class="review-badge">${isCorrect ? "正解" : "要復習"}</span>`;
    item.addEventListener("click", () => { state.current = index; state.submitted = false; showScreen(examScreen); renderQuestion(); startTimer(); });
    list.appendChild(item);
  });
  showScreen(resultScreen);
}

async function startExam() {
  $("#start-button").disabled = true;
  try {
    await loadQuestions();
    state.current = 0;
    state.answers = {};
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

$("#start-button").addEventListener("click", startExam);
$("#prev-button").addEventListener("click", () => { if (state.current > 0) { state.current -= 1; renderQuestion(); } });
$("#next-button").addEventListener("click", () => { if (state.current === state.questions.length - 1) submitExam(); else { state.current += 1; renderQuestion(); } });
$("#restart-button").addEventListener("click", () => { showScreen(startScreen); $(".timer").style.color = "var(--blue-deep)"; });
