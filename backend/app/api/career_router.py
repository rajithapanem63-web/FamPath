"""Career roadmap and student skill development API router."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_payload
from app.models.career import StudentCareerGoal
from app.services.workspace_service import get_workspace_for_user

router = APIRouter(prefix="/career-roadmap", tags=["Career Roadmap"])


# ── Domain Rule-Based Roadmap Definitions ─────────────────────────────────────

CAREER_TRACKS: dict[str, dict[str, Any]] = {
    "CSE": {
        "Full-Stack Web Development": {
            "description": "Design and build modern web applications from responsive frontends to scalable cloud backends.",
            "skills": [
                {"name": "JavaScript / TypeScript", "category": "Languages", "level": "Core"},
                {"name": "HTML5, CSS3 & Tailwind", "category": "Frontend", "level": "Core"},
                {"name": "React / Next.js", "category": "Frontend", "level": "Core"},
                {"name": "Node.js / Express or FastAPI", "category": "Backend", "level": "Core"},
                {"name": "PostgreSQL & Prisma/SQLAlchemy", "category": "Database", "level": "Core"},
                {"name": "Git, Docker & CI/CD", "category": "DevOps", "level": "Intermediate"},
            ],
            "roadmap": [
                {
                    "stage": 1,
                    "title": "Semester 1-2: Programming & Web Basics",
                    "milestones": [
                        {"id": "cse_fs_1", "text": "Master JavaScript fundamentals (ES6+, async/await, closures)"},
                        {"id": "cse_fs_2", "text": "Build responsive web layouts using semantic HTML & modern CSS/Tailwind"},
                        {"id": "cse_fs_3", "text": "Learn Git version control and GitHub workflow basics"},
                    ],
                },
                {
                    "stage": 2,
                    "title": "Semester 3-4: Modern Frontend & APIs",
                    "milestones": [
                        {"id": "cse_fs_4", "text": "Build dynamic component-based UIs with React and TypeScript"},
                        {"id": "cse_fs_5", "text": "Design RESTful APIs with FastAPI or Express with token authentication"},
                        {"id": "cse_fs_6", "text": "Model relational databases with PostgreSQL and write performant queries"},
                    ],
                },
                {
                    "stage": 3,
                    "title": "Semester 5-6: Full-Stack Architecture",
                    "milestones": [
                        {"id": "cse_fs_7", "text": "Implement state management, client caching, and server-side rendering"},
                        {"id": "cse_fs_8", "text": "Containerize full-stack apps with Docker and Docker Compose"},
                        {"id": "cse_fs_9", "text": "Set up automated unit and integration tests with Playwright / Pytest"},
                    ],
                },
                {
                    "stage": 4,
                    "title": "Semester 7-8: Production & Cloud Deployment",
                    "milestones": [
                        {"id": "cse_fs_10", "text": "Deploy microservices with CI/CD pipelines to AWS or Render"},
                        {"id": "cse_fs_11", "text": "Implement Redis caching, rate limiting, and observability"},
                        {"id": "cse_fs_12", "text": "Complete an open-source capstone project and technical portfolio"},
                    ],
                },
            ],
            "beginner_projects": [
                {"title": "Student Task & Budget Tracker", "desc": "CRUD app with local storage, categories, and charts."},
                {"title": "Campus Club Portal", "desc": "Role-based event registration system with JWT auth and email alerts."},
                {"title": "Markdown Technical Blog", "desc": "Static site generation with Next.js, search, and dark mode."},
            ],
        },
        "Data Science & AI / ML": {
            "description": "Extract insights from complex data, engineer predictive algorithms, and deploy machine learning models.",
            "skills": [
                {"name": "Python & NumPy / Pandas", "category": "Languages & Data", "level": "Core"},
                {"name": "Linear Algebra & Statistics", "category": "Mathematics", "level": "Core"},
                {"name": "Scikit-Learn & ML Pipelines", "category": "Machine Learning", "level": "Core"},
                {"name": "PyTorch or TensorFlow", "category": "Deep Learning", "level": "Intermediate"},
                {"name": "FastAPI Model Serving", "category": "MLOps", "level": "Intermediate"},
            ],
            "roadmap": [
                {
                    "stage": 1,
                    "title": "Semester 1-2: Mathematics & Python Mastery",
                    "milestones": [
                        {"id": "cse_ds_1", "text": "Master Python for data analysis, vector operations in NumPy, and Pandas dataframes"},
                        {"id": "cse_ds_2", "text": "Cover probability, descriptive statistics, and linear algebra fundamentals"},
                        {"id": "cse_ds_3", "text": "Perform Exploratory Data Analysis (EDA) on Kaggle datasets using Matplotlib/Seaborn"},
                    ],
                },
                {
                    "stage": 2,
                    "title": "Semester 3-4: Classical Machine Learning",
                    "milestones": [
                        {"id": "cse_ds_4", "text": "Implement regression, classification, clustering, and cross-validation with Scikit-Learn"},
                        {"id": "cse_ds_5", "text": "Understand tree-based ensembles: Random Forests and XGBoost / LightGBM"},
                        {"id": "cse_ds_6", "text": "Learn feature engineering, handling missing data, and evaluation metrics (ROC-AUC, F1)"},
                    ],
                },
                {
                    "stage": 3,
                    "title": "Semester 5-6: Deep Learning & NLP/Vision",
                    "milestones": [
                        {"id": "cse_ds_7", "text": "Build neural networks in PyTorch: CNNs for vision, RNNs/Transformers for text"},
                        {"id": "cse_ds_8", "text": "Explore model explainability using SHAP and LIME"},
                        {"id": "cse_ds_9", "text": "Wrap trained models in FastAPI endpoints for real-time inference"},
                    ],
                },
                {
                    "stage": 4,
                    "title": "Semester 7-8: MLOps & Capstone Pipeline",
                    "milestones": [
                        {"id": "cse_ds_10", "text": "Set up experiment tracking with MLflow and model registry"},
                        {"id": "cse_ds_11", "text": "Build an end-to-end RAG pipeline or recommendation system"},
                        {"id": "cse_ds_12", "text": "Publish reproducibility package and research/technical writeup"},
                    ],
                },
            ],
            "beginner_projects": [
                {"title": "Student Exam Score Predictor", "desc": "Linear regression and feature importance on historical study metrics."},
                {"title": "Fake News & Sentiment Classifier", "desc": "TF-IDF + Naive Bayes/Logistic Regression text classification."},
                {"title": "Heart Disease Risk Assessment App", "desc": "Trained classification model deployed as an interactive Streamlit app."},
            ],
        },
    },
    "ECE": {
        "Embedded Systems & IoT": {
            "description": "Design firmware and connect smart hardware devices to cloud networks.",
            "skills": [
                {"name": "Embedded C / C++", "category": "Languages", "level": "Core"},
                {"name": "Microcontrollers (ARM Cortex / ESP32)", "category": "Hardware", "level": "Core"},
                {"name": "Communication Protocols (UART, SPI, I2C, MQTT)", "category": "Protocols", "level": "Core"},
                {"name": "FreeRTOS", "category": "RTOS", "level": "Intermediate"},
            ],
            "roadmap": [
                {
                    "stage": 1,
                    "title": "Semester 1-2: Circuit Analysis & C Programming",
                    "milestones": [
                        {"id": "ece_iot_1", "text": "Master pointers, memory layouts, and bit manipulation in C"},
                        {"id": "ece_iot_2", "text": "Understand digital logic circuits, timers, ADC, and interrupts"},
                        {"id": "ece_iot_3", "text": "Program Arduino / 8051 GPIOs and sensor readouts"},
                    ],
                },
                {
                    "stage": 2,
                    "title": "Semester 3-4: ARM Microcontrollers & Peripherals",
                    "milestones": [
                        {"id": "ece_iot_4", "text": "Interface I2C, SPI, and UART peripherals on ESP32 or STM32"},
                        {"id": "ece_iot_5", "text": "Develop multi-tasking applications with FreeRTOS"},
                        {"id": "ece_iot_6", "text": "Transmit sensor telemetry over WiFi/BLE via MQTT to cloud brokers"},
                    ],
                },
                {
                    "stage": 3,
                    "title": "Semester 5-6: PCB Design & Low-Power Optimization",
                    "milestones": [
                        {"id": "ece_iot_7", "text": "Design custom two-layer schematics and PCB layouts in KiCad"},
                        {"id": "ece_iot_8", "text": "Implement deep sleep modes and power budget calculations"},
                        {"id": "ece_iot_9", "text": "Write secure OTA (Over-The-Air) firmware update routines"},
                    ],
                },
                {
                    "stage": 4,
                    "title": "Semester 7-8: Edge AI & Industrial IoT",
                    "milestones": [
                        {"id": "ece_iot_10", "text": "Deploy TinyML models on microcontrollers for gesture/audio detection"},
                        {"id": "ece_iot_11", "text": "Interface with industrial Modbus / CAN bus networks"},
                        {"id": "ece_iot_12", "text": "Fabricate and test a production-ready smart IoT hardware product"},
                    ],
                },
            ],
            "beginner_projects": [
                {"title": "Smart Home Weather Station", "desc": "ESP32 reading DHT22 and sending live telemetry to cloud dashboard."},
                {"title": "Automated Plant Irrigation System", "desc": "Soil moisture sensing with relay pump control and low battery alert."},
                {"title": "RFID Smart Attendance Tracker", "desc": "Log card taps with timestamp to Google Sheets / cloud database."},
            ],
        },
    },
    "MECH": {
        "CAD / CAM & Product Design": {
            "description": "Model mechanical components, simulate stress behaviors, and prepare manufacturing workflows.",
            "skills": [
                {"name": "SolidWorks / Fusion 360", "category": "CAD", "level": "Core"},
                {"name": "Engineering Mechanics & GD&T", "category": "Theory", "level": "Core"},
                {"name": "ANSYS FEA / CFD", "category": "Simulation", "level": "Intermediate"},
                {"name": "Additive Manufacturing (3D Printing)", "category": "Manufacturing", "level": "Core"},
            ],
            "roadmap": [
                {
                    "stage": 1,
                    "title": "Semester 1-2: Engineering Graphics & Fundamentals",
                    "milestones": [
                        {"id": "mech_cad_1", "text": "Learn orthographic projections and isometric engineering drawings"},
                        {"id": "mech_cad_2", "text": "Master parametric 2D sketching and 3D solid modeling in Fusion 360"},
                        {"id": "mech_cad_3", "text": "Understand material properties, stress-strain curves, and factor of safety"},
                    ],
                },
                {
                    "stage": 2,
                    "title": "Semester 3-4: Assembly & GD&T Standards",
                    "milestones": [
                        {"id": "mech_cad_4", "text": "Model multi-part assemblies with realistic constraints and motion joints"},
                        {"id": "mech_cad_5", "text": "Apply Geometric Dimensioning and Tolerancing (GD&T) per ASME Y14.5"},
                        {"id": "mech_cad_6", "text": "Slice and 3D print functional prototypes with FDM printers"},
                    ],
                },
                {
                    "stage": 3,
                    "title": "Semester 5-6: Finite Element Analysis (FEA)",
                    "milestones": [
                        {"id": "mech_cad_7", "text": "Perform static structural stress and deflection simulations in ANSYS"},
                        {"id": "mech_cad_8", "text": "Conduct thermal heat dissipation and flow analysis on mechanical heatsinks"},
                        {"id": "mech_cad_9", "text": "Optimize part topology for light-weighting and strength-to-weight ratio"},
                    ],
                },
                {
                    "stage": 4,
                    "title": "Semester 7-8: Production & Manufacturing Validation",
                    "milestones": [
                        {"id": "mech_cad_10", "text": "Generate G-code for CNC milling and turning operations in CAM software"},
                        {"id": "mech_cad_11", "text": "Perform Design for Manufacturing and Assembly (DFMA) audits"},
                        {"id": "mech_cad_12", "text": "Deliver a complete mechanical mechanism design with simulation dossier"},
                    ],
                },
            ],
            "beginner_projects": [
                {"title": "Multi-Ratio Gearbox Model", "desc": "Design and 3D print an interconnected spur gear transmission."},
                {"title": "Universal Drone Frame Optimization", "desc": "Lightweight quadcopter arm design analyzed under maximum thrust loads."},
                {"title": "Ergonomic Hand Gripper Mechanism", "desc": "Spring-loaded compliant mechanism modeled with stress analysis."},
            ],
        },
    },
}

# Fallback for other branches (EEE, CIVIL, etc.)
DEFAULT_TRACK = {
    "Core Engineering & Software Proficiency": {
        "description": "Combine branch engineering fundamentals with technical computing, data tools, and project management.",
        "skills": [
            {"name": "Python & Technical Computing", "category": "Software", "level": "Core"},
            {"name": "Domain Engineering Software", "category": "Domain", "level": "Core"},
            {"name": "Data Analysis & Excel/BI", "category": "Analytics", "level": "Core"},
            {"name": "Project Management & Safety Standards", "category": "Management", "level": "Intermediate"},
        ],
        "roadmap": [
            {
                "stage": 1,
                "title": "Semester 1-2: Core Engineering & Computation",
                "milestones": [
                    {"id": "def_1", "text": "Master core branch fundamentals and mathematics"},
                    {"id": "def_2", "text": "Learn Python programming for engineering simulations and data parsing"},
                    {"id": "def_3", "text": "Document technical labs and problem-solving methodologies"},
                ],
            },
            {
                "stage": 2,
                "title": "Semester 3-4: Domain Software & Toolchains",
                "milestones": [
                    {"id": "def_4", "text": "Gain proficiency in industry-standard branch design software"},
                    {"id": "def_5", "text": "Analyze branch-specific datasets and test benchmarks"},
                    {"id": "def_6", "text": "Execute a hands-on laboratory miniature project"},
                ],
            },
            {
                "stage": 3,
                "title": "Semester 5-6: System Design & Automation",
                "milestones": [
                    {"id": "def_7", "text": "Integrate software monitoring with physical domain systems"},
                    {"id": "def_8", "text": "Study regulatory standards, environmental codes, and safety protocols"},
                    {"id": "def_9", "text": "Publish a comprehensive project technical report"},
                ],
            },
            {
                "stage": 4,
                "title": "Semester 7-8: Capstone & Industry Placement",
                "milestones": [
                    {"id": "def_10", "text": "Complete major capstone solving a real-world industrial constraint"},
                    {"id": "def_11", "text": "Prepare portfolio and technical interview problem-solving bank"},
                    {"id": "def_12", "text": "Participate in inter-college innovation or hackathon challenges"},
                ],
            },
        ],
        "beginner_projects": [
            {"title": "Automated Energy / Sensor Logger", "desc": "Log and plot operational measurements using Python scripts."},
            {"title": "Branch Design Optimization Dossier", "desc": "Parametric calculation spreadsheet and safety factor verification."},
            {"title": "Mini Solar / IoT Monitoring Unit", "desc": "Real-time dashboard displaying power and load telemetry."},
        ],
    }
}


class SetGoalRequest(BaseModel):
    branch_code: str = Field(min_length=2, max_length=20)
    career_role: str = Field(min_length=3, max_length=100)
    current_semester: int = Field(default=1, ge=1, le=8)


class ToggleMilestoneRequest(BaseModel):
    milestone_id: str


@router.get("/{workspace_id}", summary="Get active career roadmap")
async def get_career_roadmap(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Returns the student's active roadmap, skills, milestones, and beginner projects."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    result = await db.execute(
        select(StudentCareerGoal).where(
            StudentCareerGoal.workspace_id == workspace_id,
            StudentCareerGoal.user_id == token.user_id,
        )
    )
    goal = result.scalar_one_or_none()

    # Available tracks dictionary for selection
    available_options: dict[str, list[str]] = {
        branch: list(roles.keys()) for branch, roles in CAREER_TRACKS.items()
    }
    available_options["EEE"] = ["Power Electronics & EV Systems", "Industrial Automation"]
    available_options["CIVIL"] = ["Structural Engineering & BIM", "Smart Infrastructure"]

    if not goal:
        return {
            "has_goal": False,
            "available_options": available_options,
            "default_branch": "CSE",
            "message": "Set your engineering branch and career goal to generate your roadmap.",
        }

    branch_data = CAREER_TRACKS.get(goal.branch_code.upper(), DEFAULT_TRACK)
    track_data = branch_data.get(goal.career_role) or list(branch_data.values())[0]

    completed = goal.completed_milestones or []
    all_milestones = [m["id"] for stage in track_data["roadmap"] for m in stage["milestones"]]
    progress_pct = round((len(completed) / len(all_milestones)) * 100, 1) if all_milestones else 0.0

    return {
        "has_goal": True,
        "branch_code": goal.branch_code,
        "career_role": goal.career_role,
        "current_semester": goal.current_semester,
        "completed_milestones": completed,
        "progress_percent": progress_pct,
        "description": track_data.get("description", ""),
        "skills": track_data.get("skills", []),
        "roadmap": track_data.get("roadmap", []),
        "beginner_projects": track_data.get("beginner_projects", []),
        "available_options": available_options,
    }


@router.post("/{workspace_id}", status_code=status.HTTP_201_CREATED, summary="Set student career goal")
async def set_career_goal(
    workspace_id: uuid.UUID,
    data: SetGoalRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Creates or updates student's preferred branch and career role."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    result = await db.execute(
        select(StudentCareerGoal).where(
            StudentCareerGoal.workspace_id == workspace_id,
            StudentCareerGoal.user_id == token.user_id,
        )
    )
    goal = result.scalar_one_or_none()

    if goal:
        goal.branch_code = data.branch_code.upper()
        goal.career_role = data.career_role
        goal.current_semester = data.current_semester
    else:
        goal = StudentCareerGoal(
            workspace_id=workspace_id,
            user_id=token.user_id,
            branch_code=data.branch_code.upper(),
            career_role=data.career_role,
            current_semester=data.current_semester,
            completed_milestones=[],
        )
        db.add(goal)

    await db.commit()
    return {"message": "Career goal saved", "branch_code": goal.branch_code, "career_role": goal.career_role}


@router.put("/{workspace_id}/milestones/{milestone_id}", summary="Toggle completed roadmap milestone")
async def toggle_milestone(
    workspace_id: uuid.UUID,
    milestone_id: str,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Toggles completion state of a milestone."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    result = await db.execute(
        select(StudentCareerGoal).where(
            StudentCareerGoal.workspace_id == workspace_id,
            StudentCareerGoal.user_id == token.user_id,
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail={"error_code": "CAREER_GOAL_NOT_SET"})

    current_list = list(goal.completed_milestones or [])
    if milestone_id in current_list:
        current_list.remove(milestone_id)
        is_completed = False
    else:
        current_list.append(milestone_id)
        is_completed = True

    goal.completed_milestones = current_list
    await db.commit()

    return {"milestone_id": milestone_id, "is_completed": is_completed, "total_completed": len(current_list)}
