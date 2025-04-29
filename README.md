
# Employee Records Django App

A simple Django application for managing patient session records, with Excel import and ngrok exposure. These instructions assume **Windows** and no virtual‐environment steps.

---

## 1. Download & Install

1. **Download the repository**  

     ```powershell
     git clone https://github.com/AlyaF3i/center_data_entry.git
     cd center_data_entry
     ```

2. **Install Python dependencies**  
   Open PowerShell (as normal user) in the project root and run:  

   ```powershell
   pip install -r requirements.txt
   ```

---

## 2. Configure Settings

1. **Run Ngrok**:

    ```Powershell
    ngrok http 8000
    # it will print for you a url
    # Forwarding  https://7393-2001-8f8-1c3b-1260-1caf-2afb-931c-818c.ngrok-free.app -> http://localhost:8000
    ```

2. **Set your ngrok domain** (In `employee_site\settings.py`):  

   ```python
   DOMAIN = "YOUR-NGROK-HOST.ngrok-free.app" # you get it from the output of the previous step
   ```

## 3. Database Setup

Run these commands in PowerShell from the project root:

```powershell
# python manage.py makemigrations # only if you update the models.py
python manage.py migrate
```

This creates the SQLite database and all required tables.

---

## 4. Create Admin User

Create a Django superuser to access the admin panel:

```powershell
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

---

## 5. Import Files & PaymentTypes

Use the management command to load your Excel sheet:

```powershell
python manage.py import_sheet "C:\Users\user\Desktop\ram_help\DAILY ACTIVE PED.xlsx" "Sheet1"
```

This will:

- Create (or reuse) each **File** by the `FILE` column.
- Create (or reuse) each **PaymentType** by the `(TRX, COMP)` values.

---

## 6. Run Locally

Start the Django development server on port 8000:

```powershell
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## 7. Expose via ngrok

1. **Download ngrok for Windows** from  
   https://ngrok.com/download  
   and unzip `ngrok.exe` into a folder, e.g., `C:\ngrok`.

2. **Run ngrok** (in a separate PowerShell window):  
   ```powershell
   C:\ngrok\ngrok.exe http 8000
   ```

3. **Copy** the forwarding URL that ngrok prints, e.g.:  
   ```
   Forwarding                    https://7393-2001-8f8-1c3b-1260-1caf-2afb-931c-818c.ngrok-free.app -> localhost:8000
   ```

4. **Update** `DOMAIN` in `settings.py` with that host (see Step 2), then **restart** the Django server.

---

## 8. Access & Admin

- **App UI**: `https://<your-ngrok-host>/`  
- **Admin UI**: `https://<your-ngrok-host>/admin/`

Log in with your superuser credentials to manage Files, PaymentTypes, and EmployeeRecords.

---

You’re now ready to use and share your Django app publicly via ngrok!