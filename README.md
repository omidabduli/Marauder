# Marauder

A traffic-light board for team workload. Everyone marks how loaded they are for the current two weeks, so whoever hands out work can see who has room and who needs relief.

**Project page and live demo:** https://omidabduli.github.io/Marauder/

## Statuses

| Status | Meaning | Rule of thumb |
|---|---|---|
| Green · Super | Room in the schedule, happy to help | under 70 % |
| Yellow · OK | Busy but under control; check before assigning more | 70–85 % |
| Orange · Full | No new tasks; may need to hand something off | 85–100 % |
| Red · Overloaded | At the limit or blocked; needs help now | over 100 % |

Each status also has its own shape (square, circle, hatched, triangle), so the board reads without colour.

## Features

- Board of people by group, one column per two-week period, with the current period marked and future periods shown ahead
- Summary of the current period at the top, naming everyone who is red
- A new period starts with each person's last status
- Admin page (`/admin`, password protected): language, past-week edit lock and limit, number of future periods, admin password
- Built-in help with 30 questions and answers from `ampel_faq.csv` (German)
- Interface in German, English, French and Italian
- Data in one CSV file; the server keeps the most recent 16 week columns

## Run it

Needs Python 3.7 or newer.

```bash
git clone https://github.com/omidabduli/Marauder.git
cd Marauder
pip install -r requirements.txt
python server.py
```

Open http://localhost:5005. Colleagues on the same network use the address the server prints at start-up. On macOS or Windows you can double-click `RUN_MARAUDER.command` or `RUN_MARAUDER.bat` instead; both set up a virtual environment first.

The admin password starts as `admin`. Change it on the admin page before the team uses the board.

## Files

```text
Marauder/
├── Interface.html          The board
├── admin.html              Admin settings
├── server.py               Flask server and API
├── users.csv               People, groups and statuses (sample data)
├── ampel_faq.csv           Help questions and answers
├── requirements.txt
├── RUN_MARAUDER.command    macOS launcher
├── RUN_MARAUDER.bat        Windows launcher
├── site/index.html         Project page for GitHub Pages
└── .github/workflows/      Builds and deploys the Pages site
```

## GitHub Pages demo

The Pages site uses the same `Interface.html` and `admin.html`. When no server answers, both pages switch to a demo: a sample team with fictional names, statuses generated around the current date, and changes kept in the visitor's browser.

---

Omid Abduli · [github.com/omidabduli](https://github.com/omidabduli)
