# Food Donation and Redistribution Portal

A beginner-friendly college mini project using HTML, CSS, JavaScript, Flask, and MySQL.

## Features
- Registration and login with hashed passwords.
- Roles: Donor, NGO, Volunteer, Admin.
- Post and search available food donations.
- NGO requests, donor approval/rejection, and delivery status updates.
- Deadline checks: expired donations are not listed or approved.
- Admin can review users and verify NGOs/volunteers.
- Dashboard and summary statistics.

## Requirements
- Python 3.10+
- MySQL Server and MySQL Workbench (optional)
- A browser

## Setup (Windows)
1. Extract the ZIP and open the `food_donation_portal` folder in VS Code.
2. Open a terminal in this folder.
3. Create and activate a virtual environment:
   ```powershell
   py -m venv venv
   .\venv\Scripts\activate
   ```
4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Start MySQL Server. In MySQL Workbench, open `schema.sql` and execute it.
6. Set your database password in the environment. In PowerShell (for this terminal only):
   ```powershell
   $env:DB_USER="root"
   $env:DB_PASSWORD="your_mysql_password"
   $env:DB_NAME="food_donation_portal"
   $env:SECRET_KEY="replace-this-with-a-long-random-secret"
   ```
   If your MySQL root account has no password, set `$env:DB_PASSWORD=""`.
7. Create the first admin account using the one-time helper below, then run the app.

### Create an admin account
Run:
```powershell
py create_admin.py
```
Enter the admin name, email and password when prompted. Keep this account private.

8. Start the website:
   ```powershell
   py app.py
   ```
9. Visit `http://127.0.0.1:5000`.

## Demo workflow
1. Log in as Admin and verify an NGO and Volunteer after they register.
2. Register a Donor, log in, and create a donation with a future safe-consumption deadline.
3. Log in as the verified NGO and request that donation.
4. Log back in as the Donor and approve/reject the request.
5. Log in as a verified Volunteer and update pickup/delivery status.

## Food safety notes
- Only donate food that has been handled, stored, and transported safely.
- Enter truthful preparation time and a conservative safe-consumption deadline.
- This demo blocks deadlines in the past, but it cannot verify food condition or temperature.
- Do not donate food that smells unusual, is spoiled, contaminated, or has unknown storage history.
- Keep food covered, prevent cross-contamination, and use suitable temperature control.
- Follow applicable local food-safety rules. This software is not a food-safety certification.

## Important
- This is an educational prototype, not a production-ready service.
- Before public deployment, use HTTPS, a strong secret key, CSRF protection, rate limiting, secure cookie settings, logging, backups, and proper authorization testing.
- `debug=True` is for local development only. Turn it off in production.
