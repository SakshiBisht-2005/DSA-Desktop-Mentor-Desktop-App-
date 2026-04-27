# DSA Mentor Studio

`DSA Mentor Studio` is a Python desktop application for guided Data Structures and Algorithms preparation. It combines a strict mentor flow with a LeetCode-style practice workspace.

## What Changed

The app now includes:

- Multi-user login and signup with securely hashed passwords
- SQLite-backed progress, tests, notes, bookmarks, and auto-saved practice drafts
- Top navigation: `Dashboard`, `Topics`, `Practice`, `Tests`, `Profile`
- Beginner onboarding tutorial and button tooltips
- Dark mode and light mode
- A three-panel practice workspace:
  - left: expandable roadmap and problem browser
  - center: problem description, constraints, examples, hints, solution
  - right: syntax-highlighted editor, run preview, submit flow, output console
- Search and difficulty filtering for problems
- Random `Practice Mode` from completed topics
- A strict mentor system:
  - sequential unlocks
  - automatic tests after 2 distinct study days
  - fail -> revise -> retake gating

## DSA Coverage

The seeded roadmap now covers 15 major tracks:

1. Arrays
2. Strings
3. Linked List
4. Stack
5. Queue
6. Recursion & Backtracking
7. Searching & Sorting
8. Hashing
9. Two Pointers / Sliding Window
10. Trees
11. Heap / Priority Queue
12. Graphs
13. Dynamic Programming
14. Greedy Algorithms
15. Bit Manipulation

Each topic includes:

- concept explanation
- time complexity
- space complexity
- real-world intuition
- alternative approaches
- interview explanation tips
- selected language implementation example
- 10 curated LeetCode-style practice problems

## Project Structure

```text
main.py
app/
  core/          # config, models, database, password security
  data/          # DSA curriculum and problem bank
  repositories/  # SQLite persistence layer
  services/      # auth, mentor, course, question engine
  ui/            # desktop UI shell and theme system
  ui/components/ # syntax editor and tooltips
data/
  dsa_mentor.db  # auto-created SQLite database
```

## Run The App

Use a normal local Python 3.11 or 3.12 installation with `tkinter` enabled.

```powershell
python -c "import tkinter; print('tkinter-ok')"
python main.py
```

## Validation Notes

The service layer was smoke-tested in this workspace for:

- user signup
- roadmap initialization
- search and random practice selection
- run preview
- practice submission
- automatic mentor test creation

The Codex bundled runtime here can compile the Tkinter code, but its embedded Tk/Tcl environment still could not open the actual desktop window in-thread. The application is intended to be launched with a normal local Python installation that has Tkinter working.
