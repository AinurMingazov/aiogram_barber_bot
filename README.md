### Installing
```
git clone https://github.com/AinurMingazov/aiogram_barber_bot
cd aiogram_barber_bot
```
Then create .env file (or rename and modify .env.example) in project root and set environment variables for application.

---
This example of a Telegram bot on aiogram3 was developed for a barber,
but can be applied in any field where recording is needed.

The functionality allows you to make a record for date and time. 
Added restrictions for recording such as: holidays, weekends,
filled days and one user can have only one active booking.
The calendar functionality was taken from [aiogram_calendar](https://github.com/noXplode/aiogram_calendar),
with the MIT license, because it was necessary to designate dates, so we did not use it as a library,
but added it to the repository with modifications.

At this stage the solution is done minimally to make it work...
