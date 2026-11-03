from fastapi import APIRouter
from backend.database import get_db_connection

router = APIRouter(prefix="/api/college", tags=["College Hub"])

@router.get("/info")
def get_college_info():
    return {
        "name": "Chandigarh Group of Colleges (CGC), Landran",
        "established": 2000,
        "location": "Sector 112, Landran, Greater Mohali, Punjab - 140307",
        "affiliation": "I.K. Gujral Punjab Technical University (IKGPTU), Jalandhar",
        "approvals": ["AICTE", "PCI", "NAAC A++ Accredited", "NBA Accredited Programs"],
        "campus_area": "110+ Acres with state-of-the-art academic blocks, research centres, sports complexes, and Wi-Fi enabled hostel facilities",
        "official_website": "https://www.cgc.edu.in",
        "library_url": "https://www.cgc.edu.in/library",
        "ptu_url": "https://ptu.ac.in",
        "ptu_syllabus_url": "https://ptu.ac.in/syllabus"
    }

@router.get("/departments")
def get_departments():
    return {
        "institution": "Chandigarh Group of Colleges (CGC), Landran",
        "constituent_institutes": [
            {
                "name": "Chandigarh Engineering College (CEC)",
                "accreditation": "NAAC A++ Grade, NBA Accredited Programs",
                "departments": [
                    {
                        "department_name": "Department of Computer Science & Engineering",
                        "courses": [
                            "Computer Science Engineering (CSE)",
                            "Artificial Intelligence and Machine Learning (AI & ML)",
                            "Artificial Intelligence and Data Science (AI & DS)",
                            "CSE — Data Science",
                            "CSE — Cyber Security",
                            "CSE — IoT and Cyber Security, including Blockchain",
                            "M.Tech in CSE"
                        ]
                    },
                    {
                        "department_name": "Department of Information Technology",
                        "courses": [
                            "Information Technology (IT)",
                            "M.Tech in IT"
                        ]
                    },
                    {
                        "department_name": "Department of Electronics & Communication Engineering",
                        "courses": [
                            "Electronics and Communication Engineering (ECE)",
                            "Electronic and Computer Engineering",
                            "M.Tech in ECE"
                        ]
                    },
                    {
                        "department_name": "Department of Mechanical Engineering",
                        "courses": [
                            "Mechanical Engineering",
                            "M.Tech in Mechanical Engineering"
                        ]
                    },
                    {
                        "department_name": "Department of Robotics & Advanced Engineering",
                        "courses": [
                            "Robotics and Artificial Intelligence"
                        ]
                    },
                    {
                        "department_name": "Lateral Entry Wing",
                        "courses": [
                            "B.Tech lateral-entry (LEET) options"
                        ]
                    }
                ]
            },
            {
                "name": "Chandigarh Business School of Administration (CBSA)",
                "departments": [
                    {
                        "department_name": "Department of Computer Applications",
                        "courses": [
                            "BCA — Bachelor of Computer Applications",
                            "BCA LEET",
                            "MCA — Master of Computer Applications"
                        ]
                    },
                    {
                        "department_name": "Department of Management Studies",
                        "courses": [
                            "BBA",
                            "MBA",
                            "MBA in Digital Marketing"
                        ]
                    },
                    {
                        "department_name": "Department of Commerce",
                        "courses": [
                            "B.Com. (Hons.)"
                        ]
                    }
                ]
            },
            {
                "name": "Chandigarh College of Pharmacy (CCP)",
                "accreditation": "Pharmacy Council of India (PCI) Approved, AICTE",
                "departments": [
                    {
                        "department_name": "Department of Pharmaceutical Sciences",
                        "courses": [
                            "B.Pharm",
                            "B.Pharm LEET",
                            "Pharm.D",
                            "Pharm.D (Post Baccalaureate)",
                            "M.Pharm in Pharmaceutics",
                            "M.Pharm in Pharmacology",
                            "M.Pharm in Pharmacy Practice",
                            "M.Pharm in Regulatory Affairs"
                        ]
                    }
                ]
            },
            {
                "name": "Chandigarh College of Hotel Management and Catering Technology (CCHMCT)",
                "departments": [
                    {
                        "department_name": "Department of Hospitality and Tourism",
                        "courses": [
                            "BHMCT — Hotel Management and Catering Technology",
                            "BTTM — Bachelor of Tourism and Travel Management",
                            "BMS — Airlines, Tourism and Hospitality",
                            "B.Voc. Hospitality and Catering Management"
                        ]
                    }
                ]
            },
            {
                "name": "Science and Biotechnology Wing",
                "departments": [
                    {
                        "department_name": "Department of Biosciences & Applied Sciences",
                        "courses": [
                            "B.Sc. Biotechnology",
                            "M.Sc. Biotechnology",
                            "B.Sc. Artificial Intelligence and Machine Learning",
                            "B.Sc. Multimedia",
                            "B.Sc. Graphics and Web Designing",
                            "B.Sc. (Hons.) Nutrition and Dietetics"
                        ]
                    }
                ]
            }
        ],
        "official_url": "https://www.cgc.edu.in"
    }

@router.get("/contacts")
def get_contacts():
    return {
        "emergency_helpline": "1800 200 3575 (Toll Free)",
        "admission_counselling": ["+91-95921-04444", "+91-95921-14444", "+91-95921-24444"],
        "general_inquiry_email": "info@cgc.edu.in",
        "examination_cell_email": "examcell@cgc.edu.in",
        "registrar_office": "registrar@cgc.edu.in",
        "student_grievance": "helpdesk@cgc.edu.in",
        "training_and_placement": "crp@cgc.edu.in",
        "address": "Sector 112, Landran, Greater Mohali, Punjab - 140307",
        "official_website": "https://www.cgc.edu.in"
    }

@router.get("/placements")
def get_placements():
    return {
        "total_offers": "10,000+",
        "highest_package": "Rs. 1.14 Crore per Annum",
        "average_package": "Rs. 5.5 - 8.0 LPA across departments",
        "visiting_companies": "1,300+",
        "department_statistics": [
            {
                "category": "B.Tech (CSE & IT Core)",
                "highest_package": "Rs. 1.14 Crore",
                "average_package": "Rs. 7.5 LPA – Rs. 8.0 LPA",
                "key_recruiters": ["Amazon", "Google", "Microsoft", "Adobe", "PayPal"]
            },
            {
                "category": "B.Tech (AI & ML, AI & DS)",
                "highest_package": "Rs. 44.15 LPA",
                "average_package": "Rs. 5.77 LPA – Rs. 6.0 LPA",
                "key_recruiters": ["Tech Giants", "FinTech Teams", "Analytics Firms"]
            },
            {
                "category": "B.Tech (ECE)",
                "highest_package": "Rs. 41.00 LPA",
                "average_package": "Rs. 6.65 LPA",
                "key_recruiters": ["Samsung", "Dell", "LG Electronics", "Qualcomm"]
            },
            {
                "category": "B.Tech (Mechanical & Civil)",
                "highest_package": "Rs. 33.50 LPA",
                "average_package": "Rs. 6.00 LPA",
                "key_recruiters": ["Ashok Leyland", "Hyundai", "Maruti Suzuki", "Royal Enfield"]
            },
            {
                "category": "M.Tech (All Engineering Streams)",
                "highest_package": "Rs. 20.00 LPA",
                "average_package": "Rs. 5.44 LPA",
                "key_recruiters": ["Advanced R&D Hubs", "Core Engineering Firms"]
            },
            {
                "category": "MCA",
                "highest_package": "Rs. 36.50 LPA",
                "average_package": "Rs. 6.39 LPA",
                "key_recruiters": ["Capgemini", "IBM", "Deloitte", "Accenture", "Wipro"]
            },
            {
                "category": "BCA",
                "highest_package": "Rs. 36.50 LPA",
                "average_package": "Rs. 6.12 LPA",
                "key_recruiters": ["TCS", "Infosys", "Cognizant", "Wipro"]
            },
            {
                "category": "MBA",
                "highest_package": "Rs. 22.00 LPA",
                "average_package": "Rs. 6.67 LPA",
                "key_recruiters": ["Deloitte USI", "Bajaj Finserv", "Axis Bank", "KPMG"]
            },
            {
                "category": "BBA & B.Com",
                "highest_package": "Rs. 17.03 LPA",
                "average_package": "Rs. 5.18 LPA – Rs. 5.87 LPA",
                "key_recruiters": ["Corporate Consulting", "Retail Banking", "FinTech"]
            },
            {
                "category": "B.Pharm & M.Pharm",
                "highest_package": "Rs. 18.00 LPA",
                "average_package": "Rs. 4.21 LPA – Rs. 4.68 LPA",
                "key_recruiters": ["Cipla", "Novartis", "Sun Pharma", "Cadila"]
            },
            {
                "category": "B.Sc & M.Sc Biotechnology",
                "highest_package": "Rs. 18.00 LPA",
                "average_package": "Rs. 4.68 LPA",
                "key_recruiters": ["Healthcare Providers", "R&D Labs", "Diagnostics"]
            },
            {
                "category": "BHMCT (Hotel Management)",
                "highest_package": "Rs. 7.50 LPA",
                "average_package": "Rs. 4.50 LPA",
                "key_recruiters": ["The Oberoi Group", "Taj Hotels", "Hyatt", "Marriott"]
            },
            {
                "category": "BTTM (Travel & Tourism)",
                "highest_package": "Rs. 5.00 LPA",
                "average_package": "Rs. 2.87 LPA",
                "key_recruiters": ["Travel Management Companies", "Airlines", "Tourism Boards"]
            }
        ],
        "training": "Centralized Corporate Resource Centre (CRC) operations featuring pre-placement training modules, technical bootcamps, coding practice, and AMCAT preparations.",
        "official_portal": "https://www.cgc.edu.in/placements"
    }