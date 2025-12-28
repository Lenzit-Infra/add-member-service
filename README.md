
# Telegram Member Adder Automation (Phase 1)

This project is a Python-based automation tool designed to manage multiple Telegram accounts and perform member extraction and addition tasks securely. It utilizes `Telethon` for API interaction and a SQLAlchemy-based database for session management.

## 🚀 Phase 1 Features: Infrastructure & Session Management
- **Environment:** Fully isolated Python environment using Miniconda (No root access required).
- **Database:** SQLite database to store account details and Session Strings (replacing physical `.session` files).
- **Account Manager:** CLI script to login, handle 2FA, and save encrypted sessions to the DB.
- **ORM:** SQLAlchemy integration for scalable data modeling.

## 📂 Project Structure
```text
telegram-bot/
├── app/
│   ├── models.py       # Database schema (Accounts table)
│   └── __init__.py
├── add_account.py      # Script to add new Telegram accounts
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
````

## 🛠 Prerequisites

  - Linux Server (No sudo required)
  - Python 3.10+ (via Miniconda)
  - Telegram API ID & Hash (from [my.telegram.org](https://my.telegram.org))

## 📥 Installation

1.  **Setup Environment:**

    ```bash
    conda create -n tg_bot python=3.10 -y
    conda activate tg_bot
    ```

2.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Usage

**Adding a New Account:**
Run the following command to log in a new Telegram account and save its session to the database:

```bash
python add_account.py
```

Follow the interactive prompts to enter API ID, Hash, and the OTP code sent by Telegram.

## 🔒 Security Note

> ⚠️ **Warning:** This project uses `StringSession` to store credentials in the database (`bot_database.db`). Ensure this file is **never** committed to public repositories.

