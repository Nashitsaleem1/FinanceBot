# FinanceBot
 Developed a Telegram bot that allows users to keep track of their finances directly in Google Sheets. Through the bot, users can add records of expenses, income, and transactions between accounts directly to a Google Sheet stored in their account. Additionally, users can retrieve the current amount of finances available.


### Quickstart

To use the bot you need to complete registration. If you are already registered, you will see buttons to add expenses and income. If you are not in the database, you will see the /register button. Registration is as follows:

- Copy [Google Sheet template](https://docs.google.com/spreadsheets/d/1lO9oTJu3CudibuQCCqk-s1t3DSuRNRoty4SLY5UvG_w) to your account
- Add bot service account as an editor to your sheet: telexpense-bot@telexpense-bot.iam.gserviceaccount.com
- Start the [@telexpense_bot](https://t.me/telexpense_bot) with command /start
- Tap or type /register
- Paste link to copied Google Sheet from your account to bot chat
- Add expenses and income, they will be displayed on the "Transactions" sheet
