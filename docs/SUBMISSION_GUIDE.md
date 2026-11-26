# Submission and Git Guide (CSE 3206, CO4)

This guide follows the lab manual. Do the Git and GitHub steps yourself, because the
lab requires that the Git history shows your own contributions.

## 1. What to submit

| Item | Where it is | Done by |
|---|---|---|
| GitHub repository link | Your GitHub account | You |
| Project report (PDF) | CareSlot-Lab-Report.pdf, plus your screenshots | Project + you |
| Learning log | Section 8 of the report, filled in by you | You |
| Reflection essay (500 to 700 words) | Written in your own words | You |
| Live demo and viva (about 5 minutes) | Demo plan in Section 5 below | You |

## 2. Set up Git once

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## 3. Create the GitHub repository

1. On GitHub, click **New repository**, name it `clinic-app`, and leave README, .gitignore, and license empty.
2. In the project folder, run:

```bash
git init -b main
git add .
git commit -m "Initial project skeleton: Flask app, Factory, Repository, Strategy"
git remote add origin https://github.com/YOUR-USERNAME/clinic-app.git
git push -u origin main
```

Commit the project as it was at the start. Then build each feature as its own branch, as below.

## 4. Feature branches and commits (follow the increments in the report)

Use one branch per increment. Branch names use `feature/<short-name>`. Write the test
first, run it and see it fail, then write the code and see it pass.

| Branch | Increment | Example commit messages (write your own words) |
|---|---|---|
| `feature/booking-core` | 1. Booking, Factory, Repository, Strategy | Add appointment factory with validation; Add double-booking check |
| `feature/web-ui` | 2. Flask web interface | Add booking form and All bookings page |
| `feature/doctor-directory` | 3. Doctor profiles and search | Add doctor repository and search by name or specialty |
| `feature/doctor-view` | 4. Doctor view | Add My patients page for doctors |
| `feature/ci-lint` | 5. Ruff and CI | Add Ruff check to CI workflow |
| `feature/accounts` | 6. Accounts, roles, access control | Add patient registration and login; Add login_required decorator |
| `feature/cancel-booking` | 7. Patient cancellation | Add cancel with ownership check |
| `feature/property-tests` | Hypothesis tests | Add property tests for booking rules; Fix blank name validation; Escape search wildcards |
| `feature/doctor-approval` | 9. Doctor and admin sign-up with approval | Add doctor sign-up request; Add admin approve and reject page |
| `feature/doctor-profile` | 10. Doctor profile editing | Let doctors edit clinic and checkup times |
| `feature/sidebar-ui` | 10. Sidebar dashboard and cleaner design | Add sidebar layout for signed-in users |
| `feature/pytest-features` | New tool: pytest advanced features | Add shared fixtures; Parametrize validation tests; Add migration test with tmp_path |

Each branch flow:

```bash
git checkout main
git pull
git checkout -b feature/accounts
# write a failing test, run pytest (red), write the code, run pytest (green)
git add .
git commit -m "Add patient registration with password hashing"
git push -u origin feature/accounts
```

## 5. Pull requests, review, and merge conflict

1. On GitHub, click **Compare & pull request**. Set the base to `main`.
2. Write the description: what changed, which requirement it covers (for example, `Closes FR-12`), and how you tested it.
3. Ask a classmate to review, or review it yourself and write at least two comments.
4. Make at least one change because of a review comment: this is the "revised" case the lab asks for. Push a new commit to the same branch.
5. Have at least one pull request accepted and merged, and at least one rejected or sent back for changes. Keep the closed or rejected PR as evidence.

**Merge conflict (required):**

```bash
git checkout main
git checkout -b feature/notifier-sms
# edit clinic/notifier.py: change the print line to  print(f"[SMS to {to}] {message}")
git commit -am "Format console output as SMS"
git push -u origin feature/notifier-sms
# open a PR and merge it on GitHub

git checkout main
git checkout -b feature/notifier-email
# edit the SAME line:  print(f"[EMAIL to {to}] {message}")
git commit -am "Format console output as email"
git push -u origin feature/notifier-email
# open a PR: GitHub shows "This branch has conflicts"
git checkout feature/notifier-email
git pull origin main          # the conflict appears here
# edit the file: keep one line and delete the <<<<<<<, =======, >>>>>>> lines
git add clinic/notifier.py
git commit -m "Resolve notifier merge conflict: keep email format"
git push
```

Write a short note in the report: which lines conflicted, why, and which version you kept.

## 6. Keep the repository maintained

- README: keep the setup, test, and run steps up to date.
- Issues: create one issue per feature (for example, "Add cancellation") and close it from the PR with `Closes #1`.
- Tags: `git tag -a v1.0 -m "Final lab version"` then `git push origin v1.0`.
- Check history: `git log --oneline --graph --all` shows your branches and merges.

## 7. Continuous integration

The file `.github/workflows/ci.yml` runs Ruff and the tests on each push and pull request.
Open the **Actions** tab on GitHub after your first push. Take a screenshot of a green run.

## 8. Screenshots to take for the report

Take each one in a browser at full width, then insert it into the report under the section named.

1. Home page with doctor cards (report Section 3, prototype and UI).
2. Search result for "Cardiology" (Section 3).
3. Login page with the Patient and Doctor tabs (Section 3).
4. Patient My appointments page with a booking (Section 3).
5. Double-booking error message (Section 5, testing).
6. Doctor My patients page (Section 4).
7. Terminal showing `python -m pytest -v` passing (Section 5).
8. Terminal showing the coverage report (Section 5).
9. Terminal showing `python -m ruff check .` passing (Section 7).
10. GitHub branches page (Section 6).
11. A merged pull request with a review comment (Section 6).
12. The merge conflict message on GitHub and the resolved commit (Section 6).
13. A green Actions run for CI (Section 6).
14. Selenium test run, if Chrome is available (Section 5).

## 9. Demo plan (about 5 minutes)

1. (1 min) Show the home page and search for a doctor.
2. (1 min) Log in as a patient, book a slot, show the double-booking error.
3. (1 min) Cancel the booking and show that the slot is free again.
4. (1 min) Log in as a doctor with the Doctor tab, and show My patients.
5. (1 min) Run `python -m pytest -v` and show the tests pass; show the GitHub Actions badge.

## 10. Viva preparation

Be ready to explain:
- Why Incremental was chosen over Waterfall and Agile.
- The Factory, Repository, Decorator, and Strategy patterns: the problem each solves and the rejected alternative.
- What a mock is and where it is used.
- What Hypothesis found, and how you fixed each bug.
- Why the role check is done on the server, not only by hiding buttons.
- What the rejected alternative was for each pattern.
- The Git steps you took, including the merge conflict and the review.

Every line of code must be explained by you. AI or online code is allowed only if you can explain it in the viva, and you must state its use in the report.
