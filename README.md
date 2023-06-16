# TO DO:
- Add support for multiple-page UniHomes scraping
- Add support for Zoopla scraping
- Host on Heroku
- Change storage from local storage to MongoDB or MySQL

# Discord Web Scraper Property Finding Bot

## Summary

### Intro

This is a Discord bot that uses BeautifulSoup to scrape RightMove and UniHomes for properties in the London area and stores found properties, allowing them to be returned as strings either in Discord messages or PasteBin.

### Functionality

Basic functionality includes:

- Scraping RightMove and UniHomes
- Automatic updates every hour
- Automatic cataloguing of found properties
- Manual property removal

### Required inputs

In order to use the bot, you must have:
- Admin access to a Discord server
- Knowledge of the price per person per week (ppppw), the number of bedrooms and the number of renters for the property
- A PasteBin account

## Setup

To set up the bot and run it on your own server, follow these steps:

1. Create a [Discord app and generate a bot token](https://discordjs.guide/preparations/setting-up-a-bot-application.html#your-bot-s-token)
2. Create a PasteBin account and [generate an API token](https://pastebin.com/doc_api#1)
3. Create a `.env` file and set it up as follows:

```
DISCORD_TOKEN=yourBotToken
COMMAND_CHANNEL_ID=yourServerCommandChannel
UPDATE_CHANNEL_ID=yourServerBotMessageChannel

PASTEBIN_API_KEY=yourPasteBinAPIKey
PASTEBIN_USERNAME=yourPasteBinUsername
PASTEBIN_PASSWORD=yourPasteBinPassword
```
COMMAND_CHANNEL_ID being the Discord channel ID of the channel that you want to give the bot commands in, and UPDATE_CHANNEL_ID being the Discord channel ID of the channel that you want the bot to write messages in.

Note: These are secrets, be sure not to upload them anywhere public and store them securely.

4. [Add the bot to your server](https://discordjs.guide/preparations/adding-your-bot-to-servers.html)
5. Run script.py

If everything goes smoothly, you should get a message like this in the Discord channel you specified:
```
Bot ready! Initialise scraping with the following command: !initialise [max price per week] [number of bedrooms] [number of people]
```

6. Use the !initialise command to start the bot.

Example command usage:
```
!initialise 250 4 4
```

7. Success! The bot should be working now.