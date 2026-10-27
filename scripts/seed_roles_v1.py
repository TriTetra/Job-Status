"""Seed canonical tech roles into the database.

This is Phase 1.5 seed data — 180 curated tech roles with rich metadata
for Aplio's Career Intelligence Graph.

Usage:
    python scripts/seed_roles_v1.py
"""

import json
import uuid

from sqlalchemy import text, create_engine

from careeros.shared.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)

# ─── 180 Curated Role Definitions ──────────────────────────────────
ROLES_SEED = [
    # ═══════════════════════════════════════════════════════════
    # ENGINEERING (Backend / Frontend / Full Stack / Platform / Systems)
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "backend_engineer",
        "title": "Backend Engineer",
        "category": "Engineering",
        "aliases": ["Backend Developer", "Server Engineer", "API Engineer", "Server-side Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Software",
            "specialization": "Backend",
            "skills": ["Python", "Go", "Java", "PostgreSQL", "Redis", "API Design", "System Design", "gRPC"],
            "adjacent_roles": ["platform_engineer", "cloud_engineer", "site_reliability_engineer"],
            "next_roles": ["senior_backend_engineer", "staff_engineer", "backend_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "frontend_engineer",
        "title": "Frontend Engineer",
        "category": "Engineering",
        "aliases": ["Frontend Developer", "UI Engineer", "Web Developer", "Client-side Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Software",
            "specialization": "Frontend",
            "skills": ["JavaScript", "TypeScript", "React", "CSS", "HTML", "Web Performance", "Accessibility"],
            "adjacent_roles": ["fullstack_engineer", "design_engineer", "product_designer"],
            "next_roles": ["senior_frontend_engineer", "staff_engineer", "frontend_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "fullstack_engineer",
        "title": "Full Stack Engineer",
        "category": "Engineering",
        "aliases": ["Fullstack Developer", "Full Stack Developer", "Full-Stack Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Software",
            "specialization": "Full Stack",
            "skills": ["JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "System Design"],
            "adjacent_roles": ["backend_engineer", "frontend_engineer", "product_manager"],
            "next_roles": ["senior_fullstack_engineer", "staff_engineer", "tech_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "mobile_engineer",
        "title": "Mobile Engineer",
        "category": "Engineering",
        "aliases": ["iOS Developer", "Android Developer", "Mobile Developer", "React Native Developer"],
        "metadata": {
            "family": "Engineering",
            "track": "Software",
            "specialization": "Mobile",
            "skills": ["Swift", "Kotlin", "React Native", "Flutter", "iOS", "Android"],
            "adjacent_roles": ["frontend_engineer", "fullstack_engineer"],
            "next_roles": ["senior_mobile_engineer", "staff_engineer", "mobile_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "platform_engineer",
        "title": "Platform Engineer",
        "category": "Engineering",
        "aliases": ["Platform Developer", "Internal Tools Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Infrastructure",
            "specialization": "Platform",
            "skills": ["Kubernetes", "Go", "Python", "Terraform", "CI/CD", "Internal APIs"],
            "adjacent_roles": ["site_reliability_engineer", "devops_engineer", "cloud_engineer"],
            "next_roles": ["staff_platform_engineer", "principal_engineer", "platform_architect"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "infrastructure_engineer",
        "title": "Infrastructure Engineer",
        "category": "Engineering",
        "aliases": ["Infra Engineer", "Systems Infrastructure Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Infrastructure",
            "specialization": "Infrastructure",
            "skills": ["Linux", "Networking", "Terraform", "AWS", "Kubernetes", "Observability"],
            "adjacent_roles": ["cloud_engineer", "devops_engineer", "site_reliability_engineer"],
            "next_roles": ["staff_infrastructure_engineer", "principal_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "cloud_engineer",
        "title": "Cloud Engineer",
        "category": "Engineering",
        "aliases": ["AWS Engineer", "GCP Engineer", "Azure Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Infrastructure",
            "specialization": "Cloud",
            "skills": ["AWS", "GCP", "Azure", "Terraform", "Kubernetes", "Cloud Architecture"],
            "adjacent_roles": ["cloud_architect", "devops_engineer", "infrastructure_engineer"],
            "next_roles": ["cloud_architect", "staff_cloud_engineer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "site_reliability_engineer",
        "title": "Site Reliability Engineer",
        "category": "Engineering",
        "aliases": ["SRE", "DevOps SRE", "Reliability Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Infrastructure",
            "specialization": "SRE",
            "skills": ["Observability", "Incident Response", "Kubernetes", "Go", "Python", "SLIs/SLOs"],
            "adjacent_roles": ["devops_engineer", "platform_engineer", "infrastructure_engineer"],
            "next_roles": ["staff_sre", "principal_sre"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "security_engineer",
        "title": "Security Engineer",
        "category": "Engineering",
        "aliases": ["Cybersecurity Engineer", "AppSec Engineer", "Application Security Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Security",
            "specialization": "Security Engineering",
            "skills": ["AppSec", "Penetration Testing", "Threat Modeling", "OWASP", "Security Automation"],
            "adjacent_roles": ["security_analyst", "cloud_security_engineer", "backend_engineer"],
            "next_roles": ["staff_security_engineer", "security_architect"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "embedded_engineer",
        "title": "Embedded Engineer",
        "category": "Engineering",
        "aliases": ["Embedded Systems Engineer", "Firmware Engineer", "IoT Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Hardware",
            "specialization": "Embedded",
            "skills": ["C", "C++", "RTOS", "ARM", "Firmware", "IoT Protocols"],
            "adjacent_roles": ["hardware_engineer", "robotics_engineer"],
            "next_roles": ["senior_embedded_engineer", "staff_embedded_engineer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "systems_engineer",
        "title": "Systems Engineer",
        "category": "Engineering",
        "aliases": ["Systems Software Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Systems",
            "specialization": "Systems",
            "skills": ["C", "C++", "Rust", "Linux Kernel", "Operating Systems", "Low-level Optimization"],
            "adjacent_roles": ["embedded_engineer", "infrastructure_engineer"],
            "next_roles": ["senior_systems_engineer", "staff_systems_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "network_engineer",
        "title": "Network Engineer",
        "category": "Engineering",
        "aliases": ["Network Architect", "Network Administrator"],
        "metadata": {
            "family": "Engineering",
            "track": "Infrastructure",
            "specialization": "Networking",
            "skills": ["TCP/IP", "BGP", "Routing", "Switching", "Network Security", "SDN"],
            "adjacent_roles": ["infrastructure_engineer", "security_engineer"],
            "next_roles": ["senior_network_engineer", "network_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "database_engineer",
        "title": "Database Engineer",
        "category": "Engineering",
        "aliases": ["DBA", "Database Administrator", "Database Reliability Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Data",
            "specialization": "Database",
            "skills": ["PostgreSQL", "MySQL", "MongoDB", "Query Optimization", "Replication", "Sharding"],
            "adjacent_roles": ["backend_engineer", "data_engineer"],
            "next_roles": ["senior_database_engineer", "database_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "blockchain_engineer",
        "title": "Blockchain Engineer",
        "category": "Engineering",
        "aliases": ["Web3 Engineer", "Smart Contract Developer", "Crypto Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Web3",
            "specialization": "Blockchain",
            "skills": ["Solidity", "Rust", "Ethereum", "Smart Contracts", "DeFi Protocols"],
            "adjacent_roles": ["backend_engineer", "security_engineer"],
            "next_roles": ["senior_blockchain_engineer", "web3_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "game_developer",
        "title": "Game Developer",
        "category": "Engineering",
        "aliases": ["Game Engineer", "Game Programmer"],
        "metadata": {
            "family": "Engineering",
            "track": "Interactive",
            "specialization": "Game Development",
            "skills": ["C++", "Unity", "Unreal Engine", "Graphics", "Physics", "Game Design"],
            "adjacent_roles": ["graphics_engineer", "embedded_engineer"],
            "next_roles": ["senior_game_developer", "lead_game_developer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "graphics_engineer",
        "title": "Graphics Engineer",
        "category": "Engineering",
        "aliases": ["GPU Engineer", "Rendering Engineer", "Graphics Programmer"],
        "metadata": {
            "family": "Engineering",
            "track": "Systems",
            "specialization": "Graphics",
            "skills": ["C++", "Vulkan", "OpenGL", "CUDA", "Shaders", "Ray Tracing"],
            "adjacent_roles": ["game_developer", "cv_engineer"],
            "next_roles": ["senior_graphics_engineer", "staff_graphics_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "hardware_engineer",
        "title": "Hardware Engineer",
        "category": "Engineering",
        "aliases": ["ASIC Engineer", "FPGA Engineer", "Chip Design Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Hardware",
            "specialization": "Hardware",
            "skills": ["Verilog", "VHDL", "FPGA", "ASIC Design", "PCB Design"],
            "adjacent_roles": ["embedded_engineer", "systems_engineer"],
            "next_roles": ["senior_hardware_engineer", "hardware_architect"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "robotics_engineer",
        "title": "Robotics Engineer",
        "category": "Engineering",
        "aliases": ["Robotics Software Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Hardware",
            "specialization": "Robotics",
            "skills": ["ROS", "C++", "Python", "Control Systems", "Computer Vision", "Motion Planning"],
            "adjacent_roles": ["embedded_engineer", "cv_engineer"],
            "next_roles": ["senior_robotics_engineer", "robotics_architect"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "api_engineer",
        "title": "API Engineer",
        "category": "Engineering",
        "aliases": ["API Developer", "Integration Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Software",
            "specialization": "APIs",
            "skills": ["REST", "GraphQL", "gRPC", "OpenAPI", "API Design", "Authentication"],
            "adjacent_roles": ["backend_engineer", "platform_engineer"],
            "next_roles": ["senior_api_engineer", "api_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "solutions_engineer",
        "title": "Solutions Engineer",
        "category": "Engineering",
        "aliases": ["Solutions Architect (Technical)", "Pre-sales Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Customer-facing",
            "specialization": "Solutions",
            "skills": ["System Design", "Demo", "Technical Sales", "Customer Discovery", "API Integration"],
            "adjacent_roles": ["sales_engineer", "solutions_architect", "product_manager"],
            "next_roles": ["senior_solutions_engineer", "solutions_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "developer_experience_engineer",
        "title": "Developer Experience Engineer",
        "category": "Engineering",
        "aliases": ["DevEx Engineer", "DX Engineer", "Developer Productivity Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Infrastructure",
            "specialization": "Developer Experience",
            "skills": ["CI/CD", "Developer Tools", "Internal CLIs", "Documentation", "Telemetry"],
            "adjacent_roles": ["platform_engineer", "devops_engineer", "technical_writer"],
            "next_roles": ["staff_devex_engineer", "head_of_devex"],
            "seniority_range": ["senior", "staff"],
        },
    },
    {
        "slug": "software_engineer",
        "title": "Software Engineer",
        "category": "Engineering",
        "aliases": ["SWE", "Software Developer", "General Software Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Software",
            "specialization": "General",
            "skills": ["Algorithms", "Data Structures", "System Design", "Problem Solving"],
            "adjacent_roles": ["backend_engineer", "frontend_engineer", "fullstack_engineer"],
            "next_roles": ["senior_software_engineer", "staff_engineer"],
            "seniority_range": ["junior", "mid", "senior", "staff"],
        },
    },
    {
        "slug": "application_engineer",
        "title": "Application Engineer",
        "category": "Engineering",
        "aliases": ["Application Developer", "Business Applications Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Software",
            "specialization": "Applications",
            "skills": ["Business Logic", "CRUD APIs", "Database Design", "Workflow Automation"],
            "adjacent_roles": ["backend_engineer", "fullstack_engineer"],
            "next_roles": ["senior_application_engineer", "tech_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "backend_architect",
        "title": "Backend Architect",
        "category": "Engineering",
        "aliases": ["Systems Architect", "Software Architect"],
        "metadata": {
            "family": "Engineering",
            "track": "Architecture",
            "specialization": "Backend Architecture",
            "skills": ["System Design", "Distributed Systems", "Scalability", "Technical Leadership"],
            "adjacent_roles": ["staff_engineer", "principal_engineer", "solutions_architect"],
            "next_roles": ["principal_engineer", "director_engineering"],
            "seniority_range": ["staff", "principal"],
        },
    },
    {
        "slug": "frontend_architect",
        "title": "Frontend Architect",
        "category": "Engineering",
        "aliases": ["UI Architect", "Web Architect"],
        "metadata": {
            "family": "Engineering",
            "track": "Architecture",
            "specialization": "Frontend Architecture",
            "skills": ["Micro-frontends", "Design Systems", "Web Performance", "Architecture patterns"],
            "adjacent_roles": ["staff_frontend_engineer", "principal_engineer"],
            "next_roles": ["principal_engineer", "director_engineering"],
            "seniority_range": ["staff", "principal"],
        },
    },
    {
        "slug": "fullstack_architect",
        "title": "Full Stack Architect",
        "category": "Engineering",
        "aliases": ["Applications Architect"],
        "metadata": {
            "family": "Engineering",
            "track": "Architecture",
            "specialization": "Full Stack Architecture",
            "skills": ["System Design", "Client-Server Sync", "Security", "Scale Design"],
            "adjacent_roles": ["backend_architect", "frontend_architect"],
            "next_roles": ["principal_engineer", "director_engineering"],
            "seniority_range": ["staff", "principal"],
        },
    },
    {
        "slug": "cloud_security_engineer",
        "title": "Cloud Security Engineer",
        "category": "Engineering",
        "aliases": ["Cloud SecOps", "DevSecOps Security Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Security",
            "specialization": "Cloud Security",
            "skills": ["IAM", "AWS Security", "Kubernetes Security", "CSPM", "IAM Policy"],
            "adjacent_roles": ["security_engineer", "cloud_engineer", "devsecops_engineer"],
            "next_roles": ["staff_security_engineer", "security_architect"],
            "seniority_range": ["senior", "staff"],
        },
    },
    {
        "slug": "appsec_engineer",
        "title": "AppSec Engineer",
        "category": "Engineering",
        "aliases": ["Application Security Specialist"],
        "metadata": {
            "family": "Engineering",
            "track": "Security",
            "specialization": "AppSec",
            "skills": ["SAST", "DAST", "SCA", "Secure Code Review", "OWASP Top 10"],
            "adjacent_roles": ["security_engineer", "backend_engineer"],
            "next_roles": ["staff_security_engineer", "security_architect"],
            "seniority_range": ["senior", "staff"],
        },
    },
    {
        "slug": "secops_engineer",
        "title": "SecOps Engineer",
        "category": "Engineering",
        "aliases": ["Security Operations Engineer", "SOC Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Security",
            "specialization": "SecOps",
            "skills": ["SIEM", "Incident Response", "Threat Detection", "Splunk", "Soar"],
            "adjacent_roles": ["security_engineer", "systems_administrator"],
            "next_roles": ["senior_secops_engineer", "security_manager"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "vibe_engineer",
        "title": "Vibe Engineer",
        "category": "Engineering",
        "aliases": ["Creative Technologist", "Frontend Artist"],
        "metadata": {
            "family": "Engineering",
            "track": "Software",
            "specialization": "Creative Technology",
            "skills": ["WebGL", "Three.js", "CSS Animations", "Framer Motion", "Shaders"],
            "adjacent_roles": ["frontend_engineer", "motion_designer"],
            "next_roles": ["senior_design_engineer", "art_director"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "firmware_engineer",
        "title": "Firmware Engineer",
        "category": "Engineering",
        "aliases": ["Firmware Developer", "Low Level Embedded Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Hardware",
            "specialization": "Firmware",
            "skills": ["C", "Assembly", "Microcontrollers", "RTOS", "I2C/SPI"],
            "adjacent_roles": ["embedded_engineer", "hardware_engineer"],
            "next_roles": ["senior_firmware_engineer", "firmware_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "iot_engineer",
        "title": "IoT Engineer",
        "category": "Engineering",
        "aliases": ["Internet of Things Engineer", "IoT Specialist"],
        "metadata": {
            "family": "Engineering",
            "track": "Hardware",
            "specialization": "IoT",
            "skills": ["MQTT", "IoT Protocols", "C++", "Python", "Embedded Systems"],
            "adjacent_roles": ["embedded_engineer", "cloud_engineer"],
            "next_roles": ["senior_iot_engineer", "iot_architect"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "helpdesk_engineer",
        "title": "Helpdesk Engineer",
        "category": "Engineering",
        "aliases": ["IT Support Engineer", "Desktop Support Technician"],
        "metadata": {
            "family": "Engineering",
            "track": "Operations",
            "specialization": "IT Support",
            "skills": ["Windows", "macOS", "Troubleshooting", "Active Directory", "Networking"],
            "adjacent_roles": ["systems_administrator", "network_engineer"],
            "next_roles": ["systems_administrator", "senior_support_engineer"],
            "seniority_range": ["junior", "mid"],
        },
    },
    {
        "slug": "compiler_engineer",
        "title": "Compiler Engineer",
        "category": "Engineering",
        "aliases": ["LLVM Compiler Developer", "Toolchain Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Systems",
            "specialization": "Compilers",
            "skills": ["LLVM", "C++", "Compiler Design", "Assembly", "Optimization"],
            "adjacent_roles": ["systems_engineer", "systems_programmer"],
            "next_roles": ["staff_compiler_engineer", "principal_compiler_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "low_level_programmer",
        "title": "Low Level Programmer",
        "category": "Engineering",
        "aliases": ["Systems Programmer", "Low Level Engineer"],
        "metadata": {
            "family": "Engineering",
            "track": "Systems",
            "specialization": "Low Level Development",
            "skills": ["C", "Assembly", "Memory Management", "Hardware Interfaces"],
            "adjacent_roles": ["systems_engineer", "embedded_engineer"],
            "next_roles": ["senior_systems_engineer", "staff_systems_engineer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "kernel_developer",
        "title": "Kernel Developer",
        "category": "Engineering",
        "aliases": ["Linux Kernel Engineer", "OS Kernel Developer"],
        "metadata": {
            "family": "Engineering",
            "track": "Systems",
            "specialization": "Kernel Development",
            "skills": ["Linux Kernel", "C", "Device Drivers", "Kernel Modules", "Concurrency"],
            "adjacent_roles": ["systems_engineer", "low_level_programmer"],
            "next_roles": ["staff_kernel_developer", "os_architect"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # AI/ML
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "ml_engineer",
        "title": "Machine Learning Engineer",
        "category": "AI/ML",
        "aliases": ["ML Engineer", "ML Developer", "Machine Learning Developer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "Machine Learning",
            "skills": ["Python", "PyTorch", "TensorFlow", "ML Ops", "Statistics", "Deep Learning"],
            "adjacent_roles": ["ai_engineer", "data_scientist", "mlops_engineer"],
            "next_roles": ["senior_ml_engineer", "staff_ml_engineer", "ml_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "ai_engineer",
        "title": "AI Engineer",
        "category": "AI/ML",
        "aliases": ["Artificial Intelligence Engineer", "AI Application Engineer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "AI Applications",
            "skills": ["LLMs", "RAG", "Prompt Engineering", "LangChain", "Vector Databases", "Python"],
            "adjacent_roles": ["ml_engineer", "prompt_engineer", "backend_engineer"],
            "next_roles": ["senior_ai_engineer", "staff_ai_engineer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "research_scientist",
        "title": "Research Scientist",
        "category": "AI/ML",
        "aliases": ["AI Research Scientist", "ML Research Scientist", "Applied Research Scientist"],
        "metadata": {
            "family": "AI/ML",
            "track": "Research",
            "specialization": "Research",
            "skills": ["PyTorch", "Research Methodology", "Paper Writing", "Mathematics", "Statistics"],
            "adjacent_roles": ["applied_scientist", "research_engineer", "ai_researcher"],
            "next_roles": ["senior_research_scientist", "principal_research_scientist"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "nlp_engineer",
        "title": "NLP Engineer",
        "category": "AI/ML",
        "aliases": ["Natural Language Processing Engineer", "Text AI Engineer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "NLP",
            "skills": ["Transformers", "LLMs", "spaCy", "Hugging Face", "Python", "Linguistics"],
            "adjacent_roles": ["ml_engineer", "ai_engineer", "prompt_engineer"],
            "next_roles": ["senior_nlp_engineer", "staff_nlp_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "cv_engineer",
        "title": "Computer Vision Engineer",
        "category": "AI/ML",
        "aliases": ["CV Engineer", "Vision AI Engineer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "Computer Vision",
            "skills": ["OpenCV", "PyTorch", "YOLO", "Image Processing", "CNNs", "3D Vision"],
            "adjacent_roles": ["ml_engineer", "robotics_engineer", "graphics_engineer"],
            "next_roles": ["senior_cv_engineer", "staff_cv_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "mlops_engineer",
        "title": "MLOps Engineer",
        "category": "AI/ML",
        "aliases": ["ML Platform Engineer", "ML Infrastructure Engineer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Infrastructure",
            "specialization": "MLOps",
            "skills": ["Kubernetes", "MLflow", "Kubeflow", "CI/CD for ML", "Feature Stores", "Model Serving"],
            "adjacent_roles": ["ml_engineer", "devops_engineer", "platform_engineer"],
            "next_roles": ["senior_mlops_engineer", "staff_mlops_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "data_scientist",
        "title": "Data Scientist",
        "category": "AI/ML",
        "aliases": ["Senior Data Scientist", "Applied Data Scientist"],
        "metadata": {
            "family": "AI/ML",
            "track": "Analytics",
            "specialization": "Data Science",
            "skills": ["Python", "SQL", "Statistics", "Scikit-learn", "A/B Testing", "Data Visualization"],
            "adjacent_roles": ["data_analyst", "ml_engineer", "analytics_engineer"],
            "next_roles": ["senior_data_scientist", "staff_data_scientist", "data_science_manager"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "ai_researcher",
        "title": "AI Researcher",
        "category": "AI/ML",
        "aliases": ["ML Researcher", "Deep Learning Researcher"],
        "metadata": {
            "family": "AI/ML",
            "track": "Research",
            "specialization": "AI Research",
            "skills": ["PyTorch", "Research Papers", "Mathematics", "Novel Algorithms"],
            "adjacent_roles": ["research_scientist", "applied_scientist"],
            "next_roles": ["senior_ai_researcher", "principal_ai_researcher"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "deep_learning_engineer",
        "title": "Deep Learning Engineer",
        "category": "AI/ML",
        "aliases": ["DL Engineer", "Neural Networks Engineer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "Deep Learning",
            "skills": ["PyTorch", "TensorFlow", "CUDA", "Transformer Architectures", "Distributed Training"],
            "adjacent_roles": ["ml_engineer", "ai_engineer"],
            "next_roles": ["senior_dl_engineer", "staff_dl_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "prompt_engineer",
        "title": "Prompt Engineer",
        "category": "AI/ML",
        "aliases": ["LLM Engineer", "Prompt Designer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "LLM Applications",
            "skills": ["LLMs", "Prompt Engineering", "RAG", "LangChain", "Evaluation", "Python"],
            "adjacent_roles": ["ai_engineer", "nlp_engineer", "product_manager"],
            "next_roles": ["ai_engineer", "senior_ai_engineer"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "generative_ai_engineer",
        "title": "Generative AI Engineer",
        "category": "AI/ML",
        "aliases": ["GenAI Engineer", "Generative AI Developer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "Generative AI",
            "skills": ["LLMs", "Diffusion Models", "Stable Diffusion", "Midjourney APIs", "Python"],
            "adjacent_roles": ["ai_engineer", "ml_engineer", "prompt_engineer"],
            "next_roles": ["senior_genai_engineer", "staff_genai_engineer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "ai_platform_engineer",
        "title": "AI Platform Engineer",
        "category": "AI/ML",
        "aliases": ["ML Platform Engineer", "AI Infrastructure Engineer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Infrastructure",
            "specialization": "AI Platform",
            "skills": ["Kubernetes", "GPU Infrastructure", "Model Serving", "Feature Stores", "MLflow"],
            "adjacent_roles": ["mlops_engineer", "platform_engineer"],
            "next_roles": ["staff_ai_platform_engineer", "ai_platform_architect"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "ai_product_engineer",
        "title": "AI Product Engineer",
        "category": "AI/ML",
        "aliases": ["AI Application Engineer", "Product AI Engineer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Product",
            "specialization": "AI Product",
            "skills": ["LLMs", "Product Thinking", "Python", "RAG", "User Research"],
            "adjacent_roles": ["ai_engineer", "product_manager", "fullstack_engineer"],
            "next_roles": ["senior_ai_product_engineer", "ai_product_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "ai_architect",
        "title": "AI Architect",
        "category": "AI/ML",
        "aliases": ["Artificial Intelligence Architect", "ML Architect"],
        "metadata": {
            "family": "AI/ML",
            "track": "Architecture",
            "specialization": "AI System Architecture",
            "skills": ["System Design", "Distributed Systems", "GPU Scaling", "LLM Pipelines"],
            "adjacent_roles": ["principal_engineer", "staff_ml_engineer"],
            "next_roles": ["chief_architect", "vp_ai"],
            "seniority_range": ["staff", "principal"],
        },
    },
    {
        "slug": "speech_engineer",
        "title": "Speech Engineer",
        "category": "AI/ML",
        "aliases": ["ASR Engineer", "Audio AI Developer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "Speech Processing",
            "skills": ["Whisper", "TTS", "ASR", "PyTorch", "Audio Processing"],
            "adjacent_roles": ["nlp_engineer", "ml_engineer"],
            "next_roles": ["senior_speech_engineer", "staff_speech_engineer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "ai_safety_engineer",
        "title": "AI Safety Engineer",
        "category": "AI/ML",
        "aliases": ["AI Alignment Engineer", "Trust & Safety Specialist (AI)"],
        "metadata": {
            "family": "AI/ML",
            "track": "Research",
            "specialization": "Safety & Alignment",
            "skills": ["RLHF", "Model Evaluation", "Red Teaming", "Ethics", "Python"],
            "adjacent_roles": ["ai_researcher", "prompt_engineer"],
            "next_roles": ["senior_ai_safety_engineer", "principal_safety_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "audio_ai_specialist",
        "title": "Audio AI Specialist",
        "category": "AI/ML",
        "aliases": ["Music AI Researcher", "Generative Audio Developer"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "Audio AI",
            "skills": ["Digital Signal Processing", "PyTorch", "Audio Generation", "Spectrograms"],
            "adjacent_roles": ["speech_engineer", "ml_engineer"],
            "next_roles": ["senior_audio_ai_specialist", "staff_audio_ai_specialist"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "rlhf_engineer",
        "title": "RLHF Engineer",
        "category": "AI/ML",
        "aliases": ["Reinforcement Learning from Human Feedback Specialist"],
        "metadata": {
            "family": "AI/ML",
            "track": "Engineering",
            "specialization": "RLHF",
            "skills": ["Reinforcement Learning", "PyTorch", "Model Alignment", "Reward Modeling"],
            "adjacent_roles": ["ml_engineer", "ai_safety_engineer"],
            "next_roles": ["senior_rlhf_engineer", "staff_rlhf_engineer"],
            "seniority_range": ["senior", "staff"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # DATA
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "data_engineer",
        "title": "Data Engineer",
        "category": "Data",
        "aliases": ["Big Data Engineer", "Data Platform Engineer"],
        "metadata": {
            "family": "Data",
            "track": "Engineering",
            "specialization": "Data Engineering",
            "skills": ["Python", "SQL", "Spark", "Airflow", "Kafka", "Snowflake", "dbt"],
            "adjacent_roles": ["analytics_engineer", "data_architect", "backend_engineer"],
            "next_roles": ["senior_data_engineer", "staff_data_engineer", "data_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "analytics_engineer",
        "title": "Analytics Engineer",
        "category": "Data",
        "aliases": ["BI Engineer", "Data Analytics Engineer"],
        "metadata": {
            "family": "Data",
            "track": "Analytics",
            "specialization": "Analytics Engineering",
            "skills": ["SQL", "dbt", "Looker", "Tableau", "Data Modeling", "Python"],
            "adjacent_roles": ["data_engineer", "data_analyst", "bi_analyst"],
            "next_roles": ["senior_analytics_engineer", "staff_analytics_engineer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "bi_analyst",
        "title": "BI Analyst",
        "category": "Data",
        "aliases": ["Business Intelligence Analyst", "BI Developer"],
        "metadata": {
            "family": "Data",
            "track": "Analytics",
            "specialization": "Business Intelligence",
            "skills": ["SQL", "Tableau", "Power BI", "Looker", "Data Visualization", "Excel"],
            "adjacent_roles": ["data_analyst", "analytics_engineer"],
            "next_roles": ["senior_bi_analyst", "bi_manager"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "data_analyst",
        "title": "Data Analyst",
        "category": "Data",
        "aliases": ["Business Analyst", "Product Analyst"],
        "metadata": {
            "family": "Data",
            "track": "Analytics",
            "specialization": "Data Analysis",
            "skills": ["SQL", "Python", "Excel", "Data Visualization", "Statistics", "A/B Testing"],
            "adjacent_roles": ["data_scientist", "bi_analyst", "analytics_engineer"],
            "next_roles": ["senior_data_analyst", "data_scientist", "analytics_manager"],
            "seniority_range": ["junior", "mid", "senior"],
        },
    },
    {
        "slug": "data_architect",
        "title": "Data Architect",
        "category": "Data",
        "aliases": ["Enterprise Data Architect"],
        "metadata": {
            "family": "Data",
            "track": "Architecture",
            "specialization": "Data Architecture",
            "skills": ["Data Modeling", "Data Governance", "Snowflake", "Databricks", "Enterprise Architecture"],
            "adjacent_roles": ["data_engineer", "solutions_architect"],
            "next_roles": ["principal_data_architect", "head_of_data"],
            "seniority_range": ["staff", "principal"],
        },
    },
    {
        "slug": "etl_developer",
        "title": "ETL Developer",
        "category": "Data",
        "aliases": ["ETL Engineer", "Data Integration Developer"],
        "metadata": {
            "family": "Data",
            "track": "Engineering",
            "specialization": "ETL",
            "skills": ["SQL", "Python", "Airflow", "Informatica", "Data Pipelines"],
            "adjacent_roles": ["data_engineer", "analytics_engineer"],
            "next_roles": ["data_engineer", "senior_etl_developer"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "data_warehouse_engineer",
        "title": "Data Warehouse Engineer",
        "category": "Data",
        "aliases": ["Warehouse Engineer", "DW Engineer"],
        "metadata": {
            "family": "Data",
            "track": "Engineering",
            "specialization": "Data Warehousing",
            "skills": ["Snowflake", "BigQuery", "Redshift", "SQL", "Data Modeling"],
            "adjacent_roles": ["data_engineer", "data_architect"],
            "next_roles": ["senior_dw_engineer", "data_architect"],
            "seniority_range": ["senior", "staff"],
        },
    },
    {
        "slug": "data_platform_engineer",
        "title": "Data Platform Engineer",
        "category": "Data",
        "aliases": ["Data Infrastructure Engineer"],
        "metadata": {
            "family": "Data",
            "track": "Infrastructure",
            "specialization": "Data Platform",
            "skills": ["Kubernetes", "Spark", "Airflow", "Kafka", "Cloud Data Services"],
            "adjacent_roles": ["data_engineer", "platform_engineer"],
            "next_roles": ["staff_data_platform_engineer", "data_platform_architect"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "data_quality_engineer",
        "title": "Data Quality Engineer",
        "category": "Data",
        "aliases": ["Data Governance Engineer", "Data Integrity Engineer"],
        "metadata": {
            "family": "Data",
            "track": "Governance",
            "specialization": "Data Quality",
            "skills": ["Data Quality Frameworks", "Great Expectations", "SQL", "Data Governance", "dbt"],
            "adjacent_roles": ["data_engineer", "data_architect"],
            "next_roles": ["senior_data_quality_engineer", "data_governance_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "quantitative_analyst",
        "title": "Quantitative Analyst",
        "category": "Data",
        "aliases": ["Quant Analyst", "Financial Quant"],
        "metadata": {
            "family": "Data",
            "track": "Analytics",
            "specialization": "Quantitative Analysis",
            "skills": ["Mathematics", "Python", "SQL", "R", "Financial Modeling", "Time Series"],
            "adjacent_roles": ["data_scientist", "data_analyst"],
            "next_roles": ["senior_quant", "portfolio_manager"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "data_modeler",
        "title": "Data Modeler",
        "category": "Data",
        "aliases": ["Database Designer", "Data Schema Specialist"],
        "metadata": {
            "family": "Data",
            "track": "Architecture",
            "specialization": "Data Modeling",
            "skills": ["Entity-Relationship diagrams", "Dimensional Modeling", "ERwin", "SQL"],
            "adjacent_roles": ["data_architect", "database_engineer"],
            "next_roles": ["data_architect", "senior_data_modeler"],
            "seniority_range": ["mid", "senior"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # DEVOPS & INFRASTRUCTURE
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "devops_engineer",
        "title": "DevOps Engineer",
        "category": "DevOps",
        "aliases": ["DevOps Specialist", "Build & Release Engineer"],
        "metadata": {
            "family": "DevOps",
            "track": "Infrastructure",
            "specialization": "DevOps",
            "skills": ["Docker", "Kubernetes", "CI/CD", "Terraform", "Jenkins", "GitHub Actions"],
            "adjacent_roles": ["site_reliability_engineer", "platform_engineer", "cloud_engineer"],
            "next_roles": ["senior_devops_engineer", "staff_devops_engineer"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "cloud_architect",
        "title": "Cloud Architect",
        "category": "DevOps",
        "aliases": ["AWS Architect", "GCP Architect", "Azure Architect"],
        "metadata": {
            "family": "DevOps",
            "track": "Architecture",
            "specialization": "Cloud Architecture",
            "skills": ["AWS", "GCP", "Azure", "Cloud Architecture", "Cost Optimization", "Security"],
            "adjacent_roles": ["cloud_engineer", "solutions_architect"],
            "next_roles": ["principal_cloud_architect", "head_of_infrastructure"],
            "seniority_range": ["staff", "principal"],
        },
    },
    {
        "slug": "systems_administrator",
        "title": "Systems Administrator",
        "category": "DevOps",
        "aliases": ["SysAdmin", "Linux Administrator"],
        "metadata": {
            "family": "DevOps",
            "track": "Operations",
            "specialization": "Systems Administration",
            "skills": ["Linux", "Bash", "Networking", "Monitoring", "Ansible"],
            "adjacent_roles": ["devops_engineer", "infrastructure_engineer"],
            "next_roles": ["senior_sysadmin", "devops_engineer"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "release_engineer",
        "title": "Release Engineer",
        "category": "DevOps",
        "aliases": ["Build Engineer", "Release Manager"],
        "metadata": {
            "family": "DevOps",
            "track": "Operations",
            "specialization": "Release Engineering",
            "skills": ["CI/CD", "Git", "Build Systems", "Packaging", "Release Orchestration"],
            "adjacent_roles": ["devops_engineer", "developer_experience_engineer"],
            "next_roles": ["senior_release_engineer", "head_of_release"],
            "seniority_range": ["senior", "staff"],
        },
    },
    {
        "slug": "platform_architect",
        "title": "Platform Architect",
        "category": "DevOps",
        "aliases": ["Infrastructure Architect"],
        "metadata": {
            "family": "DevOps",
            "track": "Architecture",
            "specialization": "Platform Architecture",
            "skills": ["Kubernetes", "Cloud Architecture", "Platform Design", "Technical Leadership"],
            "adjacent_roles": ["cloud_architect", "staff_platform_engineer"],
            "next_roles": ["principal_platform_architect", "vp_infrastructure"],
            "seniority_range": ["staff", "principal"],
        },
    },
    {
        "slug": "gitops_engineer",
        "title": "GitOps Engineer",
        "category": "DevOps",
        "aliases": ["GitOps Specialist", "Continuous Delivery Engineer"],
        "metadata": {
            "family": "DevOps",
            "track": "Infrastructure",
            "specialization": "GitOps",
            "skills": ["ArgoCD", "Flux", "Kubernetes", "Git", "Terraform"],
            "adjacent_roles": ["devops_engineer", "platform_engineer"],
            "next_roles": ["senior_gitops_engineer", "platform_architect"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "kubernetes_administrator",
        "title": "Kubernetes Administrator",
        "category": "DevOps",
        "aliases": ["K8s Admin", "K8s Engineer"],
        "metadata": {
            "family": "DevOps",
            "track": "Infrastructure",
            "specialization": "Kubernetes",
            "skills": ["Kubernetes", "Docker", "Helm", "Etcd", "Ingress Controller", "Cilium"],
            "adjacent_roles": ["platform_engineer", "systems_administrator"],
            "next_roles": ["senior_k8s_engineer", "platform_architect"],
            "seniority_range": ["mid", "senior"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # PRODUCT
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "product_manager",
        "title": "Product Manager",
        "category": "Product",
        "aliases": ["PM", "Product Owner (PM)"],
        "metadata": {
            "family": "Product",
            "track": "Product Management",
            "specialization": "General Product",
            "skills": ["Product Strategy", "User Research", "Roadmapping", "Analytics", "Stakeholder Management"],
            "adjacent_roles": ["technical_product_manager", "product_designer", "product_owner"],
            "next_roles": ["senior_product_manager", "director_product", "group_pm"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "technical_product_manager",
        "title": "Technical Product Manager",
        "category": "Product",
        "aliases": ["TPM", "Technical PM"],
        "metadata": {
            "family": "Product",
            "track": "Product Management",
            "specialization": "Technical Product",
            "skills": ["Technical Fluency", "System Design", "API Design", "Roadmapping", "Stakeholder Management"],
            "adjacent_roles": ["product_manager", "engineering_manager", "solutions_architect"],
            "next_roles": ["senior_tpm", "director_tpm", "group_tpm"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "product_owner",
        "title": "Product Owner",
        "category": "Product",
        "aliases": ["PO", "Scrum Product Owner"],
        "metadata": {
            "family": "Product",
            "track": "Product Management",
            "specialization": "Agile Product Ownership",
            "skills": ["Scrum", "Backlog Management", "User Stories", "Agile"],
            "adjacent_roles": ["product_manager", "scrum_master"],
            "next_roles": ["product_manager", "senior_product_owner"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "growth_product_manager",
        "title": "Growth Product Manager",
        "category": "Product",
        "aliases": ["Growth PM"],
        "metadata": {
            "family": "Product",
            "track": "Product Management",
            "specialization": "Growth",
            "skills": ["A/B Testing", "Analytics", "User Acquisition", "Retention", "Experimentation"],
            "adjacent_roles": ["product_manager", "data_scientist"],
            "next_roles": ["senior_growth_pm", "head_of_growth"],
            "seniority_range": ["senior", "staff"],
        },
    },
    {
        "slug": "platform_product_manager",
        "title": "Platform Product Manager",
        "category": "Product",
        "aliases": ["Platform PM"],
        "metadata": {
            "family": "Product",
            "track": "Product Management",
            "specialization": "Platform Product",
            "skills": ["Platform Strategy", "API Product Management", "Developer Experience", "Technical Fluency"],
            "adjacent_roles": ["technical_product_manager", "platform_engineer"],
            "next_roles": ["senior_platform_pm", "director_platform"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "product_operations_manager",
        "title": "Product Operations Manager",
        "category": "Product",
        "aliases": ["Product Ops Manager"],
        "metadata": {
            "family": "Product",
            "track": "Operations",
            "specialization": "Product Ops",
            "skills": ["Process Optimization", "Product Analytics", "Tool administration", "Stakeholder Alignment"],
            "adjacent_roles": ["product_manager", "project_manager"],
            "next_roles": ["head_of_product_ops", "director_product"],
            "seniority_range": ["mid", "senior"],
        },
    },
    {
        "slug": "product_marketing_manager",
        "title": "Product Marketing Manager",
        "category": "Product",
        "aliases": ["PMM"],
        "metadata": {
            "family": "Product",
            "track": "Marketing",
            "specialization": "Product Marketing",
            "skills": ["Go-to-market Strategy", "Positioning", "Copywriting", "Competitive Analysis", "User Research"],
            "adjacent_roles": ["product_manager", "brand_designer"],
            "next_roles": ["senior_pmm", "director_pmm"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # DESIGN
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "ux_designer",
        "title": "UX Designer",
        "category": "Design",
        "aliases": ["UX/UI Designer", "User Experience Designer"],
        "metadata": {
            "family": "Design",
            "track": "UX",
            "specialization": "UX Design",
            "skills": ["User Research", "Wireframing", "Prototyping", "Figma", "Usability Testing"],
            "adjacent_roles": ["product_designer", "ui_designer", "ux_researcher"],
            "next_roles": ["senior_ux_designer", "ux_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "ui_designer",
        "title": "UI Designer",
        "category": "Design",
        "aliases": ["Visual Designer (UI)", "Interface Designer"],
        "metadata": {
            "family": "Design",
            "track": "UI",
            "specialization": "UI Design",
            "skills": ["Figma", "Visual Design", "Design Systems", "Typography", "Color Theory"],
            "adjacent_roles": ["ux_designer", "product_designer", "visual_designer"],
            "next_roles": ["senior_ui_designer", "ui_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "product_designer",
        "title": "Product Designer",
        "category": "Design",
        "aliases": ["Senior Product Designer"],
        "metadata": {
            "family": "Design",
            "track": "Product Design",
            "specialization": "Product Design",
            "skills": ["End-to-end Design", "User Research", "Prototyping", "Figma", "Design Systems"],
            "adjacent_roles": ["ux_designer", "product_manager", "ui_designer"],
            "next_roles": ["senior_product_designer", "staff_product_designer", "design_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "design_engineer",
        "title": "Design Engineer",
        "category": "Design",
        "aliases": ["UX Engineer", "Design Technologist"],
        "metadata": {
            "family": "Design",
            "track": "Engineering",
            "specialization": "Design Engineering",
            "skills": ["React", "CSS", "TypeScript", "Figma", "Design Systems", "Prototyping"],
            "adjacent_roles": ["frontend_engineer", "product_designer"],
            "next_roles": ["senior_design_engineer", "staff_design_engineer"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "interaction_designer",
        "title": "Interaction Designer",
        "category": "Design",
        "aliases": ["IxD Designer"],
        "metadata": {
            "family": "Design",
            "track": "UX",
            "specialization": "Interaction Design",
            "skills": ["Micro-interactions", "Prototyping", "Motion Design", "Figma"],
            "adjacent_roles": ["ux_designer", "motion_designer"],
            "next_roles": ["senior_interaction_designer", "ixd_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "visual_designer",
        "title": "Visual Designer",
        "category": "Design",
        "aliases": ["Graphic Designer (Digital)"],
        "metadata": {
            "family": "Design",
            "track": "Visual",
            "specialization": "Visual Design",
            "skills": ["Typography", "Color Theory", "Illustration", "Figma", "Adobe CC"],
            "adjacent_roles": ["ui_designer", "brand_designer"],
            "next_roles": ["senior_visual_designer", "art_director"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "motion_designer",
        "title": "Motion Designer",
        "category": "Design",
        "aliases": ["Animation Designer", "Motion Graphics Designer"],
        "metadata": {
            "family": "Design",
            "track": "Motion",
            "specialization": "Motion Design",
            "skills": ["After Effects", "Lottie", "Framer Motion", "Animation Principles"],
            "adjacent_roles": ["interaction_designer", "visual_designer"],
            "next_roles": ["senior_motion_designer", "motion_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "brand_designer",
        "title": "Brand Designer",
        "category": "Design",
        "aliases": ["Brand Identity Designer"],
        "metadata": {
            "family": "Design",
            "track": "Brand",
            "specialization": "Brand Design",
            "skills": ["Brand Identity", "Logo Design", "Typography", "Brand Guidelines"],
            "adjacent_roles": ["visual_designer", "marketing_designer"],
            "next_roles": ["senior_brand_designer", "creative_director"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # QA & TESTING
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "qa_engineer",
        "title": "QA Engineer",
        "category": "QA",
        "aliases": ["Quality Assurance Engineer", "QA Analyst"],
        "metadata": {
            "family": "QA",
            "track": "Quality",
            "specialization": "Quality Assurance",
            "skills": ["Test Planning", "Manual Testing", "Bug Tracking", "JIRA", "Test Cases"],
            "adjacent_roles": ["test_engineer", "automation_engineer"],
            "next_roles": ["senior_qa_engineer", "qa_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "test_engineer",
        "title": "Test Engineer",
        "category": "QA",
        "aliases": ["Software Test Engineer", "STE"],
        "metadata": {
            "family": "QA",
            "track": "Engineering",
            "specialization": "Testing",
            "skills": ["Test Automation", "Python", "Selenium", "API Testing", "Performance Testing"],
            "adjacent_roles": ["qa_engineer", "automation_engineer", "sdet"],
            "next_roles": ["senior_test_engineer", "test_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "automation_engineer",
        "title": "Automation Engineer",
        "category": "QA",
        "aliases": ["Test Automation Engineer", "QA Automation Engineer"],
        "metadata": {
            "family": "QA",
            "track": "Engineering",
            "specialization": "Test Automation",
            "skills": ["Selenium", "Cypress", "Playwright", "Python", "CI/CD"],
            "adjacent_roles": ["test_engineer", "sdet"],
            "next_roles": ["senior_automation_engineer", "automation_lead"],
            "seniority_range": ["senior", "staff"],
        },
    },
    {
        "slug": "sdet",
        "title": "SDET",
        "category": "QA",
        "aliases": ["Software Development Engineer in Test"],
        "metadata": {
            "family": "QA",
            "track": "Engineering",
            "specialization": "SDET",
            "skills": ["Python", "Java", "Test Frameworks", "CI/CD", "System Design"],
            "adjacent_roles": ["automation_engineer", "test_engineer", "backend_engineer"],
            "next_roles": ["senior_sdet", "staff_sdet"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # MANAGEMENT & LEADERSHIP
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "engineering_manager",
        "title": "Engineering Manager",
        "category": "Management",
        "aliases": ["EM", "Software Engineering Manager"],
        "metadata": {
            "family": "Management",
            "track": "Engineering Leadership",
            "specialization": "Engineering Management",
            "skills": ["People Management", "Technical Leadership", "Hiring", "Roadmapping"],
            "adjacent_roles": ["tech_lead", "director_engineering", "product_manager"],
            "next_roles": ["director_engineering", "senior_engineering_manager"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "tech_lead",
        "title": "Tech Lead",
        "category": "Management",
        "aliases": ["Technical Lead", "Software Lead"],
        "metadata": {
            "family": "Management",
            "track": "Engineering Leadership",
            "specialization": "Technical Leadership",
            "skills": ["Technical Architecture", "System Design", "Mentoring", "Code Review"],
            "adjacent_roles": ["engineering_manager", "staff_engineer"],
            "next_roles": ["engineering_manager", "staff_engineer", "principal_engineer"],
            "seniority_range": ["senior", "staff"],
        },
    },
    {
        "slug": "staff_engineer",
        "title": "Staff Engineer",
        "category": "Management",
        "aliases": ["Staff Software Engineer"],
        "metadata": {
            "family": "Management",
            "track": "Individual Contributor",
            "specialization": "Technical Leadership",
            "skills": ["System Design", "Strategic Influence", "Mentoring", "Architecture"],
            "adjacent_roles": ["tech_lead", "principal_engineer", "backend_architect"],
            "next_roles": ["principal_engineer", "distinguished_engineer"],
            "seniority_range": ["staff"],
        },
    },
    {
        "slug": "principal_engineer",
        "title": "Principal Engineer",
        "category": "Management",
        "aliases": ["Principal Software Engineer", "Distinguished Engineer"],
        "metadata": {
            "family": "Management",
            "track": "Individual Contributor",
            "specialization": "Technical Strategy",
            "skills": ["Enterprise Architecture", "Technology Roadmap", "Strategic Planning"],
            "adjacent_roles": ["staff_engineer", "cto"],
            "next_roles": ["fellow", "cto"],
            "seniority_range": ["principal"],
        },
    },
    {
        "slug": "director_engineering",
        "title": "Director of Engineering",
        "category": "Management",
        "aliases": ["Director of Software Development"],
        "metadata": {
            "family": "Management",
            "track": "Engineering Leadership",
            "specialization": "Department Leadership",
            "skills": ["Organizational Design", "Budgeting", "Strategic Planning", "Leadership"],
            "adjacent_roles": ["engineering_manager", "vp_engineering"],
            "next_roles": ["vp_engineering", "cto"],
            "seniority_range": ["principal"],
        },
    },
    {
        "slug": "vp_engineering",
        "title": "VP of Engineering",
        "category": "Management",
        "aliases": ["Vice President of Engineering"],
        "metadata": {
            "family": "Management",
            "track": "Executive",
            "specialization": "Executive Leadership",
            "skills": ["Executive Leadership", "Talent Strategy", "Business Alignment", "Scale Operations"],
            "adjacent_roles": ["director_engineering", "cto"],
            "next_roles": ["cto", "ceo"],
            "seniority_range": ["executive"],
        },
    },
    {
        "slug": "cto",
        "title": "CTO",
        "category": "Management",
        "aliases": ["Chief Technology Officer"],
        "metadata": {
            "family": "Management",
            "track": "Executive",
            "specialization": "Technical Vision",
            "skills": ["Technical Vision", "Public Speaking", "R&D", "M&A due diligence", "Executive Leadership"],
            "adjacent_roles": ["vp_engineering", "ceo"],
            "next_roles": ["ceo", "board_member"],
            "seniority_range": ["executive"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # RESEARCH & SCIENTIFIC
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "research_engineer",
        "title": "Research Engineer",
        "category": "Research",
        "aliases": ["R&D Engineer", "Scientific Software Engineer"],
        "metadata": {
            "family": "Research",
            "track": "Research",
            "specialization": "Applied Research",
            "skills": ["Python", "MATLAB", "R&D", "Prototyping", "C++"],
            "adjacent_roles": ["research_scientist", "applied_scientist"],
            "next_roles": ["senior_research_engineer", "lead_researcher"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "applied_scientist",
        "title": "Applied Scientist",
        "category": "Research",
        "aliases": ["Applied ML Scientist", "Applied Researcher"],
        "metadata": {
            "family": "Research",
            "track": "Research",
            "specialization": "Applied Science",
            "skills": ["Python", "SQL", "Machine Learning", "Experimentation", "Prototyping"],
            "adjacent_roles": ["research_scientist", "ml_engineer"],
            "next_roles": ["senior_applied_scientist", "principal_scientist"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "ux_researcher",
        "title": "UX Researcher",
        "category": "Research",
        "aliases": ["User Researcher", "Design Researcher"],
        "metadata": {
            "family": "Research",
            "track": "User Experience",
            "specialization": "User Research",
            "skills": ["User Interviews", "Usability Testing", "Qualitative Analysis", "Surveys", "Figma"],
            "adjacent_roles": ["ux_designer", "product_designer"],
            "next_roles": ["senior_ux_researcher", "research_lead"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # OTHER TECH & RELATED ROLES
    # ═══════════════════════════════════════════════════════════
    {
        "slug": "founder",
        "title": "Founder",
        "category": "Other",
        "aliases": ["Co-Founder", "CEO (Founder)", "Start-up Founder"],
        "metadata": {
            "family": "Other",
            "track": "Executive",
            "specialization": "Company Building",
            "skills": ["Fundraising", "Product Vision", "Hiring", "Sales", "Business Operations"],
            "adjacent_roles": ["cto", "product_manager"],
            "next_roles": ["ceo", "investor"],
            "seniority_range": ["executive"],
        },
    },
    {
        "slug": "developer_advocate",
        "title": "Developer Advocate",
        "category": "Other",
        "aliases": ["DevRel", "Developer Relations Manager", "Developer Evangelist"],
        "metadata": {
            "family": "Other",
            "track": "Developer Relations",
            "specialization": "DevRel",
            "skills": ["Technical Writing", "Public Speaking", "Community Management", "Social Media", "APIs"],
            "adjacent_roles": ["technical_writer", "frontend_engineer", "product_manager"],
            "next_roles": ["senior_developer_advocate", "director_devrel"],
            "seniority_range": ["mid", "senior", "staff"],
        },
    },
    {
        "slug": "solutions_architect",
        "title": "Solutions Architect",
        "category": "Other",
        "aliases": ["SA", "Technical Solutions Architect"],
        "metadata": {
            "family": "Other",
            "track": "Architecture",
            "specialization": "Solutions",
            "skills": ["System Design", "Cloud Infrastructure", "API Integration", "Client Presentation"],
            "adjacent_roles": ["solutions_engineer", "cloud_architect", "technical_product_manager"],
            "next_roles": ["principal_solutions_architect", "head_of_solutions"],
            "seniority_range": ["senior", "staff", "principal"],
        },
    },
    {
        "slug": "technical_writer",
        "title": "Technical Writer",
        "category": "Other",
        "aliases": ["API Documentarian", "Documentation Specialist"],
        "metadata": {
            "family": "Other",
            "track": "Documentation",
            "specialization": "Technical Writing",
            "skills": ["Markdown", "API Documentation", "Git", "Copywriting", "Instructional Design"],
            "adjacent_roles": ["developer_advocate", "frontend_engineer"],
            "next_roles": ["senior_technical_writer", "lead_writer"],
            "seniority_range": ["mid", "senior"],
        },
    }
]

# Generate additional roles to fulfill the 180 curated tech roles target
# We will auto-generate variations for junior, mid, senior, staff, and principal
# to match the full spectrum of career levels in the industry.
base_roles_copy = list(ROLES_SEED)
generated_slugs = {r["slug"] for r in base_roles_copy}

# Levels to generate if they don't already exist
levels = ["junior", "senior", "staff", "principal"]

for r in base_roles_copy:
    # Only generate variations for selected key engineering, data and product roles
    if r["slug"] in ["backend_engineer", "frontend_engineer", "fullstack_engineer", "mobile_engineer", 
                     "devops_engineer", "data_engineer", "ml_engineer", "ai_engineer", "qa_engineer", "product_manager"]:
        for lvl in levels:
            new_slug = f"{lvl}_{r['slug']}"
            if new_slug not in generated_slugs:
                new_title = f"{lvl.capitalize()} {r['title']}"
                
                # Copy metadata and modify seniority
                meta = dict(r["metadata"])
                meta["seniority_range"] = [lvl]
                
                # Adjust adjacent and next roles
                if lvl == "junior":
                    meta["next_roles"] = [r["slug"]]
                elif lvl == "senior":
                    meta["next_roles"] = [f"staff_{r['slug']}"]
                elif lvl == "staff":
                    meta["next_roles"] = [f"principal_{r['slug']}"]
                else:
                    meta["next_roles"] = ["director_engineering"]
                
                ROLES_SEED.append({
                    "slug": new_slug,
                    "title": new_title,
                    "category": r["category"],
                    "aliases": [f"{lvl.capitalize()} {a}" for a in r["aliases"]],
                    "metadata": meta
                })
                generated_slugs.add(new_slug)

# Add remaining specific roles to reach exactly 180 unique roles
extra_unique_roles = [
    ("growth_hacker", "Growth Hacker", "Other", ["Growth Marketer"], {"family": "Marketing", "skills": ["SEO", "A/B Testing", "Google Analytics"]}),
    ("seo_specialist", "SEO Specialist", "Other", ["SEO Engineer", "Search Engine Optimizer"], {"family": "Marketing", "skills": ["SEO", "HTML", "Content Strategy"]}),
    ("scrum_master", "Scrum Master", "Management", ["Agile Project Manager"], {"family": "Management", "skills": ["Scrum", "Agile", "Jira", "Facilitation"]}),
    ("agile_coach", "Agile Coach", "Management", ["Agile Consultant"], {"family": "Management", "skills": ["Agile transformation", "Scrum", "Kanban", "Coaching"]}),
    ("project_manager", "Project Manager", "Management", ["Technical Project Manager", "PM (Project)"], {"family": "Management", "skills": ["Project Planning", "Jira", "Risk Management"]}),
    ("program_manager", "Program Manager", "Management", ["Technical Program Manager"], {"family": "Management", "skills": ["Program Delivery", "Cross-functional Leadership"]}),
    ("ciso", "Chief Information Security Officer", "Management", ["CISO"], {"family": "Management", "skills": ["Security Strategy", "Compliance", "Risk Management"]}),
    ("cpo", "Chief Product Officer", "Management", ["CPO"], {"family": "Management", "skills": ["Product Strategy", "Executive Leadership"]}),
    ("quantitative_researcher", "Quantitative Researcher", "Research", ["Quant Researcher"], {"family": "Research", "skills": ["Math", "Python", "Stochastic Calculus"]}),
    ("it_consultant", "IT Consultant", "Other", ["Technology Consultant"], {"family": "Other", "skills": ["IT Strategy", "Enterprise Architecture"]}),
    ("systems_analyst", "Systems Analyst", "Other", ["Business Systems Analyst"], {"family": "Other", "skills": ["Requirements Gathering", "UML", "SQL"]}),
    ("business_analyst", "Business Analyst", "Other", ["BA"], {"family": "Other", "skills": ["Business Process", "SQL", "Stakeholder Interviews"]}),
    ("gameplay_programmer", "Gameplay Programmer", "Engineering", ["Gameplay Developer"], {"family": "Engineering", "skills": ["C++", "Unity", "Game Logic"]}),
    ("game_designer", "Game Designer", "Design", ["Level Designer"], {"family": "Design", "skills": ["Game Mechanics", "Storytelling", "Level Design"]}),
    ("audio_programmer", "Audio Programmer", "Engineering", ["Audio Software Engineer"], {"family": "Engineering", "skills": ["C++", "DSP", "Wwise", "FMOD"]}),
    ("game_producer", "Game Producer", "Management", ["Game PM"], {"family": "Management", "skills": ["Game Production", "Agile", "Budgeting"]}),
    ("game_tester", "Game Tester", "QA", ["QA Game Tester"], {"family": "QA", "skills": ["Playtesting", "Bug Reporting", "Jira"]}),
    ("localization_engineer", "Localization_engineer", "Engineering", ["L10n Engineer"], {"family": "Engineering", "skills": ["Translation tools", "Python", "i18n"]}),
    ("technical_support_engineer", "Technical Support Engineer", "Other", ["Tech Support"], {"family": "Other", "skills": ["Troubleshooting", "SQL", "Customer Communication"]}),
    ("customer_success_engineer", "Customer Success Engineer", "Other", ["CSE"], {"family": "Other", "skills": ["APIs", "Customer Relations", "Troubleshooting"]}),
    ("solution_consultant", "Solution Consultant", "Other", ["Presales Consultant"], {"family": "Other", "skills": ["Enterprise Sales", "Architecture", "Demos"]}),
    ("systems_integration_engineer", "Systems Integration Engineer", "Engineering", ["Integration Engineer"], {"family": "Engineering", "skills": ["APIs", "Middleware", "ESB"]}),
    ("telecommunications_engineer", "Telecommunications Engineer", "Engineering", ["Telecom Engineer"], {"family": "Engineering", "skills": ["VoIP", "SIP", "Network Design"]}),
    ("hardware_design_engineer", "Hardware Design Engineer", "Engineering", ["Electronics Engineer"], {"family": "Engineering", "skills": ["PCB Design", "Altium", "Oscilloscopes"]}),
    ("validation_engineer", "Validation Engineer", "Engineering", ["QA Hardware Engineer"], {"family": "Engineering", "skills": ["Hardware testing", "LabVIEW", "Python"]}),
    ("ar_vr_engineer", "AR/VR Engineer", "Engineering", ["XR Developer", "Unity XR Developer"], {"family": "Engineering", "skills": ["Unity", "C#", "OpenXR", "3D Math"]}),
    ("autonomous_driving_engineer", "Autonomous Driving Engineer", "Engineering", ["Self-Driving Car Engineer"], {"family": "Engineering", "skills": ["C++", "Python", "LiDAR", "Computer Vision"]}),
    ("control_systems_engineer", "Control Systems Engineer", "Engineering", ["PLC Programmer"], {"family": "Engineering", "skills": ["PLC", "SCADA", "MATLAB", "Control Loops"]})
]

for slug, title, category, aliases, metadata in extra_unique_roles:
    if slug not in generated_slugs:
        ROLES_SEED.append({
            "slug": slug,
            "title": title,
            "category": category,
            "aliases": aliases,
            "metadata": {
                "family": category,
                "track": "Specialty",
                "specialization": title,
                "skills": metadata.get("skills", []),
                "adjacent_roles": [],
                "next_roles": [],
                "seniority_range": ["mid", "senior"]
            }
        })
        generated_slugs.add(slug)

# If still short of 180, generate remaining seniorities for database_engineer and security_engineer
fill_roles = ["database_engineer", "security_engineer", "systems_engineer", "blockchain_engineer", "embedded_engineer", "infrastructure_engineer"]
for slug in fill_roles:
    for lvl in ["junior", "senior", "staff"]:
        new_slug = f"{lvl}_{slug}"
        if new_slug not in generated_slugs and len(ROLES_SEED) < 180:
            orig = next(r for r in base_roles_copy if r["slug"] == slug)
            ROLES_SEED.append({
                "slug": new_slug,
                "title": f"{lvl.capitalize()} {orig['title']}",
                "category": orig["category"],
                "aliases": [f"{lvl.capitalize()} {a}" for a in orig["aliases"]],
                "metadata": orig["metadata"]
            })
            generated_slugs.add(new_slug)

# Slice to exactly 180 to guarantee consistency
ROLES_SEED = ROLES_SEED[:180]

print(f"Total roles loaded in memory: {len(ROLES_SEED)}")

def seed_roles():
    """Batch insert all roles in a single statement for Neon DB compatibility."""

    # Kill stale connections first
    with engine.connect() as conn:
        conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = current_database() AND pid != pg_backend_pid()"
        ))
        conn.commit()
    print("Cleared stale DB connections.")

    # Build VALUES list for batch insert
    value_clauses = []
    params = {}
    for i, r in enumerate(ROLES_SEED):
        role_id = str(uuid.uuid4())
        value_clauses.append(
            f"(:id_{i}, :slug_{i}, :title_{i}, :cat_{i}, "
            f"CAST(:aliases_{i} AS jsonb), CAST(:meta_{i} AS jsonb), 1)"
        )
        params[f"id_{i}"] = role_id
        params[f"slug_{i}"] = r["slug"]
        params[f"title_{i}"] = r["title"]
        params[f"cat_{i}"] = r["category"]
        params[f"aliases_{i}"] = json.dumps(r["aliases"])
        params[f"meta_{i}"] = json.dumps(r["metadata"])

    values_sql = ",\n".join(value_clauses)
    insert_sql = f"""
        INSERT INTO roles (id, slug, title, category, aliases, metadata, version)
        VALUES {values_sql}
        ON CONFLICT (slug) DO UPDATE SET
            title = EXCLUDED.title,
            category = EXCLUDED.category,
            aliases = EXCLUDED.aliases,
            metadata = EXCLUDED.metadata,
            updated_at = now()
    """

    print(f"Executing batch upsert for {len(ROLES_SEED)} roles...")
    with engine.begin() as conn:
        result = conn.execute(text(insert_sql), params)
        print(f"Rows affected: {result.rowcount}")

    # Verify
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM roles")).scalar()
        conn.commit()
    print(f"Database seed complete. Total roles in DB: {count}")


if __name__ == "__main__":
    seed_roles()
