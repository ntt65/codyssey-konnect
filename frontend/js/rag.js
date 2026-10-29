import { requestJSON, formatApiError } from "./http.js";

const form = document.getElementById("ask-form");
const question = document.getElementById("question");
const messages = document.getElementById("messages");
const send = document.getElementById("send");
const clear = document.getElementById("clear");
const status = document.getElementById("status");
const initialMessages = messages.innerHTML;
const idle = status.textContent;
// Same-origin by default. Separate frontend hosting can set this public URL.
const apiBase = window.RAG_API_BASE || "";

function message(role, text, error = false) {
  const article = document.createElement("article");
  article.className = "message " + role + (error ? " error" : "");
  const title = document.createElement("strong");
  title.textContent = role === "user" ? "나" : "도우미";
  const body = document.createElement("p");
  body.textContent = text;
  article.append(title, body);
  messages.append(article);
  return article;
}

clear.addEventListener("click", () => {
  messages.innerHTML = initialMessages;
  status.textContent = idle;
  question.focus();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value || send.disabled) return;
  message("user", value);
  send.disabled = true;
  clear.disabled = true;
  question.disabled = true;
  status.textContent = "관련 자료를 찾고 답변을 준비하고 있어요…";
  messages.setAttribute("aria-busy", "true");
  try {
    const result = await requestJSON(apiBase + "/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: value }),
    });
    const article = message("assistant", result.answer);
    if (result.citations.length) {
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = "참고 자료 " + result.citations.length + "개";
      details.append(summary);
      result.citations.forEach((citation, i) => {
        const source = document.createElement("p");
        source.textContent = "[" + (i + 1) + "] " + citation.source;
        const snippet = document.createElement("blockquote");
        snippet.textContent = citation.snippet;
        details.append(source, snippet);
      });
      article.append(details);
    }
    question.value = "";
    status.textContent = result.grounded ? "답변에 사용한 참고 자료를 확인해 보세요." : "관련 자료를 등록한 뒤 다시 질문해 주세요.";
  } catch (error) {
    message("assistant", formatApiError(error), true);
    status.textContent = "질문을 보내지 못했습니다. 다시 시도해 주세요.";
  } finally {
    messages.removeAttribute("aria-busy");
    send.disabled = false;
    clear.disabled = false;
    question.disabled = false;
    question.focus();
    messages.scrollTop = messages.scrollHeight;
  }
});
