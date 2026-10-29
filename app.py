import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).with_name("freelanceflow.db")

st.set_page_config(page_title="FreelanceFlow", page_icon="📊", layout="wide")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT NOT NULL DEFAULT '',
                hourly_rate REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Active',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS work_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                work_date TEXT NOT NULL,
                hours REAL NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                paid INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)


def query_df(sql, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def money(value):
    return f"${value:,.2f}"


init_db()
st.title("📊 FreelanceFlow")
st.caption("A lightweight workspace to track freelance projects, hours, earnings, and payment status.")

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Choose a page",
        ["Dashboard", "Projects", "Log Work", "Reports", "About"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("MVP · Local SQLite database · Sample data is optional")

projects = query_df("SELECT * FROM projects ORDER BY id DESC")
logs = query_df("""
    SELECT w.*, p.name AS project_name, p.platform, p.hourly_rate,
           w.hours * p.hourly_rate AS estimated_earnings
    FROM work_logs w
    JOIN projects p ON p.id = w.project_id
    ORDER BY w.work_date DESC, w.id DESC
""")

if page == "Dashboard":
    st.subheader("Your overview")
    if projects.empty:
        st.info("Start by adding a project on the Projects page, then record your work hours.")
        st.markdown("**Quick start**")
        st.markdown("1. Add a project and its hourly rate.\n2. Log completed work sessions.\n3. Review estimated earnings and unpaid work here.")
    else:
        total_hours = float(logs["hours"].sum()) if not logs.empty else 0.0
        total_earnings = float(logs["estimated_earnings"].sum()) if not logs.empty else 0.0
        unpaid = float(logs.loc[logs["paid"] == 0, "estimated_earnings"].sum()) if not logs.empty else 0.0
        active_projects = int((projects["status"] == "Active").sum())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Active projects", active_projects)
        c2.metric("Hours logged", f"{total_hours:,.1f}")
        c3.metric("Estimated earnings", money(total_earnings))
        c4.metric("Estimated unpaid", money(unpaid))

        if not logs.empty:
            st.subheader("Recent work")
            st.dataframe(
                logs[["work_date", "project_name", "hours", "hourly_rate", "estimated_earnings", "paid", "notes"]]
                .rename(columns={
                    "work_date": "Date", "project_name": "Project", "hours": "Hours",
                    "hourly_rate": "Rate ($/h)", "estimated_earnings": "Estimated ($)",
                    "paid": "Paid (1=yes)", "notes": "Notes"
                }),
                use_container_width=True,
                hide_index=True,
            )
            by_project = logs.groupby("project_name", as_index=False)["estimated_earnings"].sum()
            by_project = by_project.sort_values("estimated_earnings", ascending=False)
            st.subheader("Estimated earnings by project")
            st.bar_chart(by_project.set_index("project_name"))
        else:
            st.info("Your projects are ready. Log some work to see your dashboard metrics.")

elif page == "Projects":
    st.subheader("Project management")
    with st.form("add_project", clear_on_submit=True):
        name = st.text_input("Project name *", placeholder="e.g. AI evaluation project")
        platform = st.text_input("Platform / client", placeholder="e.g. Direct client, Alignerr")
        rate = st.number_input("Hourly rate (USD)", min_value=0.0, value=10.0, step=1.0)
        status = st.selectbox("Status", ["Active", "Paused", "Completed"])
        submitted = st.form_submit_button("Add project", type="primary")
        if submitted:
            if not name.strip():
                st.error("Please enter a project name.")
            else:
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO projects (name, platform, hourly_rate, status, created_at) VALUES (?, ?, ?, ?, ?)",
                        (name.strip(), platform.strip(), rate, status, date.today().isoformat()),
                    )
                st.success("Project added.")
                st.rerun()

    if not projects.empty:
        st.subheader("Saved projects")
        display = projects.rename(columns={
            "name": "Project", "platform": "Platform / client", "hourly_rate": "Rate ($/h)",
            "status": "Status", "created_at": "Created", "id": "ID"
        })
        st.dataframe(display[["ID", "Project", "Platform / client", "Rate ($/h)", "Status", "Created"]],
                     use_container_width=True, hide_index=True)
        project_to_update = st.selectbox("Change a project's status", projects["id"].tolist(),
                                         format_func=lambda pid: projects.loc[projects["id"] == pid, "name"].iloc[0])
        new_status = st.selectbox("New status", ["Active", "Paused", "Completed"], key="new_status")
        if st.button("Update status"):
            with get_connection() as conn:
                conn.execute("UPDATE projects SET status = ? WHERE id = ?", (new_status, int(project_to_update)))
            st.success("Status updated.")
            st.rerun()
    else:
        st.caption("No projects yet.")

elif page == "Log Work":
    st.subheader("Record a work session")
    if projects.empty:
        st.warning("Add a project first.")
    else:
        available = projects[projects["status"] != "Completed"]
        if available.empty:
            st.info("All projects are marked completed. Reactivate one to log work.")
        else:
            with st.form("log_work", clear_on_submit=True):
                project_id = st.selectbox(
                    "Project",
                    available["id"].tolist(),
                    format_func=lambda pid: available.loc[available["id"] == pid, "name"].iloc[0],
                )
                work_date = st.date_input("Work date", value=date.today())
                hours = st.number_input("Hours worked", min_value=0.1, max_value=24.0, value=1.0, step=0.5)
                notes = st.text_area("Notes (optional)", placeholder="What did you work on?")
                paid = st.checkbox("This work has been paid")
                submitted = st.form_submit_button("Save work log", type="primary")
                if submitted:
                    with get_connection() as conn:
                        conn.execute(
                            "INSERT INTO work_logs (project_id, work_date, hours, notes, paid) VALUES (?, ?, ?, ?, ?)",
                            (int(project_id), work_date.isoformat(), float(hours), notes.strip(), int(paid)),
                        )
                    st.success("Work session saved.")
                    st.rerun()

            if not logs.empty:
                st.subheader("Work log history")
                st.dataframe(
                    logs[["work_date", "project_name", "hours", "hourly_rate", "estimated_earnings", "paid", "notes"]]
                    .rename(columns={
                        "work_date": "Date", "project_name": "Project", "hours": "Hours",
                        "hourly_rate": "Rate ($/h)", "estimated_earnings": "Estimated ($)",
                        "paid": "Paid (1=yes)", "notes": "Notes"
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

elif page == "Reports":
    st.subheader("Reports & export")
    if logs.empty:
        st.info("Record work sessions to generate reports.")
    else:
        report = logs.copy()
        report["work_date"] = pd.to_datetime(report["work_date"])
        month = st.selectbox("Month", ["All months"] + sorted(report["work_date"].dt.strftime("%Y-%m").unique().tolist(), reverse=True))
        if month != "All months":
            report = report[report["work_date"].dt.strftime("%Y-%m") == month]
        total_hours = report["hours"].sum()
        total_estimated = report["estimated_earnings"].sum()
        total_unpaid = report.loc[report["paid"] == 0, "estimated_earnings"].sum()
        a, b, c = st.columns(3)
        a.metric("Hours", f"{total_hours:,.1f}")
        b.metric("Estimated earnings", money(total_estimated))
        c.metric("Estimated unpaid", money(total_unpaid))
        by_project = report.groupby("project_name", as_index=False).agg(
            hours=("hours", "sum"), estimated_earnings=("estimated_earnings", "sum")
        ).sort_values("estimated_earnings", ascending=False)
        st.dataframe(by_project.rename(columns={
            "project_name": "Project", "hours": "Hours", "estimated_earnings": "Estimated earnings ($)"
        }), use_container_width=True, hide_index=True)
        st.download_button(
            "Download report as CSV",
            data=report.drop(columns=["hourly_rate"], errors="ignore").to_csv(index=False).encode("utf-8"),
            file_name="freelanceflow_report.csv",
            mime="text/csv",
        )

else:
    st.subheader("About FreelanceFlow")
    st.markdown("""
    **FreelanceFlow** is an MVP for organizing freelance projects and understanding how time translates into estimated earnings.

    **Current capabilities**
    - Project creation and status management
    - Work-session logging
    - Estimated earnings and unpaid-work calculations
    - Dashboard metrics and project-level charts
    - Monthly filtering and CSV export

    **Data and privacy:** data is stored in a local SQLite database on the machine running the app. This MVP does not connect to freelance platforms or financial accounts.

    **Planned improvements:** automated tests, configurable currencies, recurring reports, CSV import, and optional AI-generated summaries.
    """)
    st.info("This tool estimates earnings from entered hours and rates. It does not verify invoices or actual payments.")
