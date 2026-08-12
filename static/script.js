const apiUrl = "http://127.0.0.1:8000/chat";
const sessionId = "default-session";

const chatWindow = document.querySelector(".chat-window");
const messageInput = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const errorBanner = document.querySelector(".error-banner");
const sessionLabel = document.querySelector(".session-id");

sessionLabel.textContent = sessionId;

function appendMessage(text, role) {
  const messageElement = document.createElement("div");
  messageElement.className = `message ${role}`;
  messageElement.textContent = text;
  chatWindow.appendChild(messageElement);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showError(text) {
  errorBanner.textContent = text;
  errorBanner.classList.add("visible");
}

function clearError() {
  errorBanner.textContent = "";
  errorBanner.classList.remove("visible");
}

async function sendMessage() {
  clearError();

  const message = messageInput.value.trim();
  if (!message) {
    showError("Please enter a message before sending.");
    return;
  }

  appendMessage(message, "user");
  messageInput.value = "";

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
      }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const errorText = body && body.detail ? body.detail : response.statusText;
      showError(`API error: ${errorText}`);
      return;
    }

    const payload = await response.json();
    appendMessage(payload.message, "agent");
  } catch (error) {
    showError(
      "Unable to reach the API. Please verify the server is running at http://127.0.0.1:8000.",
    );
  }
}

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});
