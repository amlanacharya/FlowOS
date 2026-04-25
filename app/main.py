from contextlib import asynccontextmanager
from textwrap import dedent
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers import (
    attendance,
    auth,
    branches,
    class_types,
    dashboard,
    feedback,
    leads,
    members,
    notifications,
    organizations,
    payments,
    plans,
    sessions,
    staff,
    subscriptions,
    trainer,
    workouts,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan: startup and shutdown events.
    """
    # Startup
    await create_tables()
    yield
    # Shutdown


app = FastAPI(
    title="FlowOS Gym Management API",
    version="1.0.0",
    description="Complete gym management system API",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


DOCS_PANEL_SCRIPT = dedent(
    """
    <script>
    (function () {
      const TOKEN_KEY = "flowos-docs-access-token";
      const REFRESH_KEY = "flowos-docs-refresh-token";
      const EMAIL_KEY = "flowos-docs-email";
      const SECURITY_SCHEME = "BearerAuth";

      function setStatus(message, tone) {
        const node = document.getElementById("flowos-docs-status");
        if (!node) return;
        node.textContent = message;
        node.dataset.tone = tone || "neutral";
      }

      function setBusy(isBusy) {
        const button = document.getElementById("flowos-docs-login");
        const email = document.getElementById("flowos-docs-email");
        const password = document.getElementById("flowos-docs-password");
        const clear = document.getElementById("flowos-docs-clear");
        if (!button || !email || !password || !clear) return;
        button.disabled = isBusy;
        email.disabled = isBusy;
        password.disabled = isBusy;
        clear.disabled = isBusy;
        button.textContent = isBusy ? "Signing in..." : "Login";
      }

      function applyToken(token) {
        if (!window.ui || !token) return;
        window.ui.preauthorizeApiKey(SECURITY_SCHEME, token);
      }

      function clearToken() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
        if (window.ui) {
          window.ui.authActions.logout([SECURITY_SCHEME]);
        }
        setStatus("Authorization cleared.", "neutral");
      }

      function mountPanel() {
        const root = document.getElementById("swagger-ui");
        if (!root || document.getElementById("flowos-docs-panel")) return true;

        const panel = document.createElement("section");
        panel.id = "flowos-docs-panel";
        panel.innerHTML = `
          <style>
            #flowos-docs-panel {
              margin: 16px auto 24px;
              max-width: 1460px;
              padding: 18px 20px;
              border: 1px solid #d8e1de;
              border-radius: 14px;
              background: linear-gradient(180deg, #ffffff, #f4f8f7);
              box-shadow: 0 14px 30px -24px rgba(15, 23, 42, 0.35);
              font-family: Inter, Arial, sans-serif;
            }
            #flowos-docs-panel h2 {
              margin: 0 0 6px;
              font-size: 18px;
              color: #0f172a;
            }
            #flowos-docs-panel p {
              margin: 0 0 14px;
              font-size: 13px;
              color: #475569;
            }
            #flowos-docs-form {
              display: grid;
              grid-template-columns: minmax(220px, 280px) minmax(220px, 280px) auto auto;
              gap: 10px;
              align-items: center;
            }
            #flowos-docs-form input {
              width: 100%;
              min-width: 0;
              padding: 10px 12px;
              border: 1px solid #cbd5e1;
              border-radius: 10px;
              font-size: 14px;
            }
            #flowos-docs-form button {
              padding: 10px 14px;
              border: 0;
              border-radius: 10px;
              font-size: 14px;
              font-weight: 600;
              cursor: pointer;
            }
            #flowos-docs-login {
              background: #0f766e;
              color: white;
            }
            #flowos-docs-clear {
              background: #e2e8f0;
              color: #0f172a;
            }
            #flowos-docs-status {
              margin-top: 10px;
              font-size: 13px;
              color: #475569;
            }
            #flowos-docs-status[data-tone="success"] {
              color: #166534;
            }
            #flowos-docs-status[data-tone="error"] {
              color: #b91c1c;
            }
            @media (max-width: 900px) {
              #flowos-docs-form {
                grid-template-columns: 1fr;
              }
            }
          </style>
          <h2>Session Login</h2>
          <p>Sign in once here to authorize all protected API calls in Swagger for this browser session.</p>
          <form id="flowos-docs-form">
            <input id="flowos-docs-email" type="email" placeholder="owner@fitlife.com" autocomplete="username" />
            <input id="flowos-docs-password" type="password" placeholder="OwnerPass123!" autocomplete="current-password" />
            <button id="flowos-docs-login" type="submit">Login</button>
            <button id="flowos-docs-clear" type="button">Clear</button>
          </form>
          <div id="flowos-docs-status" data-tone="neutral">Use your staff credentials to activate protected endpoints.</div>
        `;

        root.parentNode.insertBefore(panel, root);

        const emailInput = document.getElementById("flowos-docs-email");
        const passwordInput = document.getElementById("flowos-docs-password");
        const form = document.getElementById("flowos-docs-form");
        const clear = document.getElementById("flowos-docs-clear");

        emailInput.value = localStorage.getItem(EMAIL_KEY) || "owner@fitlife.com";
        passwordInput.value = "";

        form.addEventListener("submit", async function (event) {
          event.preventDefault();
          setBusy(true);
          setStatus("Signing in...", "neutral");

          const email = emailInput.value.trim();
          const password = passwordInput.value;

          try {
            const response = await fetch("/api/v1/auth/login", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ email, password })
            });

            const payload = await response.json();
            if (!response.ok) {
              throw new Error(payload.detail || "Login failed");
            }

            localStorage.setItem(TOKEN_KEY, payload.access_token);
            localStorage.setItem(REFRESH_KEY, payload.refresh_token);
            localStorage.setItem(EMAIL_KEY, email);
            applyToken(payload.access_token);
            setStatus("Authorized. Protected endpoints now use your bearer token.", "success");
          } catch (error) {
            clearToken();
            setStatus(error.message || "Login failed", "error");
          } finally {
            setBusy(false);
          }
        });

        clear.addEventListener("click", function () {
          clearToken();
        });

        const existingToken = localStorage.getItem(TOKEN_KEY);
        if (existingToken) {
          applyToken(existingToken);
          setStatus("Existing authorization restored from this browser session.", "success");
        }

        return true;
      }

      function boot() {
        if (mountPanel()) return;
        window.requestAnimationFrame(boot);
      }

      boot();
    })();
    </script>
    """
)


def build_docs_html() -> HTMLResponse:
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_ui_parameters={"persistAuthorization": True},
    )
    html = response.body.decode("utf-8")
    html = html.replace("const ui = SwaggerUIBundle({", "window.ui = SwaggerUIBundle({")
    html = html.replace("</body>", f"{DOCS_PANEL_SCRIPT}</body>")
    return HTMLResponse(content=html, status_code=response.status_code)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    return build_docs_html()


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# Mount routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(organizations.router, tags=["Organizations"])
app.include_router(branches.router, tags=["Branches"])
app.include_router(staff.router, tags=["Staff"])
app.include_router(leads.router, tags=["Leads"])
app.include_router(members.router, tags=["Members"])
app.include_router(plans.router, tags=["Plans"])
app.include_router(subscriptions.router, tags=["Subscriptions"])
app.include_router(payments.router, tags=["Payments"])
app.include_router(sessions.router, tags=["Sessions"])
app.include_router(class_types.router, tags=["Class Types"])
app.include_router(attendance.router, tags=["Attendance"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(notifications.router, tags=["Notifications"])
app.include_router(workouts.router, tags=["Workouts"])
app.include_router(feedback.router, tags=["Feedback"])
app.include_router(trainer.router, tags=["Trainer"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
