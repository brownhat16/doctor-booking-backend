import random
from typing import List, Dict, Optional
from .models import LabTest, LabPackage, LabSlot, LabOffering
from datetime import date, timedelta

class LabTestDatabase:
    def __init__(self):
        self.tests: List[LabTest] = []
        self.packages: List[LabPackage] = []
        self._seed_data()
    
    def _seed_data(self):
        """Generate mock lab tests and packages"""
        
        # Define lab centers with their characteristics
        labs = [
            {"id": "lab_001", "name": "Ruby Hall Clinic", "rating": 4.8, "location": "Pune Central", "accreditation": "NABL"},
            {"id": "lab_002", "name": "CityCare Labs", "rating": 4.5, "location": "Koregaon Park", "accreditation": "NABL"},
            {"id": "lab_003", "name": "Sahyadri Hospital", "rating": 4.7, "location": "Deccan", "accreditation": "NABL, CAP"},
            {"id": "lab_004", "name": "Deenanath Labs", "rating": 4.6, "location": "Pimpri", "accreditation": "NABL"},
            {"id": "lab_005", "name": "Apollo Diagnostics", "rating": 4.9, "location": "Shivajinagar", "accreditation": "NABL, CAP"},
        ]
        
        # Blood Tests - now with multiple lab offerings
        blood_tests_data = [
            ("CBC", "Complete Blood Count", 25, False, "No special preparation"),
            ("Lipid Profile", "Cholesterol & Triglycerides", 8, True, "12-14 hours fasting required"),
            ("Thyroid Profile", "TSH, T3, T4", 3, False, "Can be done anytime"),
            ("HbA1c", "Diabetes Monitoring", 1, False, "No fasting needed"),
            ("Liver Function Test (LFT)", "Liver Enzymes", 12, True, "8-12 hours fasting"),
            ("Kidney Function Test (KFT)", "Renal Profile", 8, True, "8 hours fasting"),
            ("Vitamin D", "Vitamin D (25-OH)", 1, False, "No preparation needed"),
            ("Vitamin B12", "B12 Levels", 1, False, "No preparation"),
            ("Iron Studies", "Serum Iron Profile", 3, True, "Morning sample preferred"),
            ("ESR", "Erythrocyte Sedimentation Rate", 1, False, "No preparation"),
            ("CRP", "C-Reactive Protein", 1, False, "No preparation"),
            ("Fasting Blood Sugar", "FBS", 1, True, "8-12 hours fasting required"),
        ]
        
        for idx, (short_name, full_name, param_count, fasting, prep) in enumerate(blood_tests_data):
            # Create lab offerings for this test (3-5 labs per test)
            import random
            num_labs = random.randint(3, 5)
            selected_labs = random.sample(labs, num_labs)
            
            lab_offerings = []
            base_price = random.choice([400, 500, 600, 700, 800, 900, 1000, 1200])
            
            for lab in selected_labs:
                # Vary price by ±20%
                price_variation = random.uniform(0.8, 1.2)
                lab_price = int(base_price * price_variation)
                
                # Vary TAT based on lab
                tat_options = ["Same day", "24 hours", "48 hours"]
                tat_weights = [0.2, 0.6, 0.2]  # 24h most common
                tat = random.choices(tat_options, weights=tat_weights)[0]
                
                # Higher rated labs slightly more expensive and faster
                if lab["rating"] >= 4.7:
                    lab_price = int(lab_price * 1.1)
                    tat = random.choice(["Same day", "24 hours"])
                
                offering = LabOffering(
                    lab_id=lab["id"],
                    lab_name=lab["name"],
                    lab_rating=lab["rating"],
                    lab_location=lab["location"],
                    price=lab_price,
                    home_collection_available=random.choice([True, True, True, False]),  # 75% yes
                    home_collection_fee=50 if random.random() > 0.3 else 0,  # Sometimes free
                    turnaround_time=tat,
                    accreditation=lab["accreditation"]
                )
                lab_offerings.append(offering)
            
            # Create test with multiple lab offerings
            test = LabTest(
                id=f"test_blood_{idx+1:03d}",
                name=full_name,
                category="Blood Tests",
                sample_type="Blood",
                fasting_required=fasting,
                preparation_instructions=prep,
                parameters_count=param_count,
                labs_offering=lab_offerings,
                rating=sum(lo.lab_rating for lo in lab_offerings) / len(lab_offerings),  # Average
                booking_count=random.randint(100, 1000)
            )
            self.tests.append(test)
        
        # Radiology Tests
        radiology_tests = [
            ("X-Ray Chest", "Chest X-Ray", "Image", False, "Remove metal objects"),
            ("X-Ray Knee", "Knee X-Ray", "Image", False, "No special preparation"),
            ("Ultrasound Abdomen", "Abdominal Ultrasound", "Image", True, "6 hours fasting, full bladder"),
            ("CT Scan Head", "Brain CT Scan", "Image", False, "Remove metal objects"),
            ("MRI Spine", "Spinal MRI", "Image", False, "Inform about implants"),
            ("ECG", "Electrocardiogram", "Graph", False, "Wear loose clothing"),
        ]
        
        for idx, (name, full_name, sample, fasting, prep) in enumerate(radiology_tests):
            test = LabTest(
                id=f"test_radio_{idx+1:03d}",
                name=full_name,
                category="Radiology",
                price=random.randint(500, 3000),
                home_collection_available=False,  # Radiology at lab only
                home_collection_fee=0,
                sample_type=sample,
                fasting_required=fasting,
                preparation_instructions=prep,
                turnaround_time="Same day",
                parameters_count=1,
                rating=round(random.uniform(4.2, 4.8), 1),
                booking_count=random.randint(50, 500)
            )
            self.tests.append(test)
        
        # Specialized Tests
        specialized_tests = [
            ("COVID-19 RT-PCR", "COVID Test", "Nasal Swab", False, "No eating/drinking 30 mins before", 1200),
            ("Dengue NS1 Antigen", "Dengue Test", "Blood", False, "No preparation", 800),
            ("Malaria Antigen", "Malaria Test", "Blood", False, "No preparation", 500),
            ("Pregnancy Test (Beta HCG)", "Pregnancy Test", "Blood", False, "Morning sample preferred", 600),
            ("Allergy Panel (Basic)", "Allergy Test", "Blood", False, "No preparation", 2500),
        ]
        
        for idx, (name, full_name, sample, fasting, prep, price) in enumerate(specialized_tests):
            test = LabTest(
                id=f"test_spec_{idx+1:03d}",
                name=full_name,
                category="Specialized Tests",
                price=price,
                home_collection_available=True,
                home_collection_fee=50,
                sample_type=sample,
                fasting_required=fasting,
                preparation_instructions=prep,
                turnaround_time="24 hours",
                parameters_count=random.randint(1, 5),
                rating=round(random.uniform(4.3, 4.9), 1),
                booking_count=random.randint(100, 800)
            )
            self.tests.append(test)
        
        # Create value-for-money packages
        self._create_packages()
    
    def _create_packages(self):
        """Create test packages with recommendations"""
        
        # Find tests by name
        def find_test(keyword):
            return next((t for t in self.tests if keyword.lower() in t.name.lower()), None)
        
        # Package 1: Full Body Checkup
        cbc = find_test("Complete Blood Count")
        lipid = find_test("Lipid Profile")
        thyroid = find_test("Thyroid Profile")
        liver = find_test("Liver Function")
        kidney = find_test("Kidney Function")
        
        if all([cbc, lipid, thyroid, liver, kidney]):
            tests = [cbc, lipid, thyroid, liver, kidney]
            original = sum(t.price for t in tests)
            package_price = int(original * 0.65)  # 35% discount
            
            pkg = LabPackage(
                id="pkg_001",
                name="Full Body Checkup",
                description="Comprehensive health screening covering all major organs",
                tests_included=[t.id for t in tests],
                original_price=original,
                package_price=package_price,
                savings=original - package_price,
                home_collection_available=True,
                home_collection_fee=50,
                category="Health Checkup",
                popular=True
            )
            self.packages.append(pkg)
        
        # Package 2: Diabetes Care Package
        hba1c = find_test("HbA1c")
        fbs = find_test("Fasting Blood Sugar")
        kidney_test = find_test("Kidney Function")
        
        if all([hba1c, fbs, kidney_test]):
            tests = [hba1c, fbs, kidney_test]
            original = sum(t.price for t in tests)
            package_price = int(original * 0.70)
            
            pkg = LabPackage(
                id="pkg_002",
                name="Diabetes Care Package",
                description="Essential tests for diabetes monitoring and management",
                tests_included=[t.id for t in tests],
                original_price=original,
                package_price=package_price,
                savings=original - package_price,
                home_collection_available=True,
                home_collection_fee=50,
                category="Diabetes",
                popular=True
            )
            self.packages.append(pkg)
        
        # Package 3: Heart Health Package
        lipid_test = find_test("Lipid Profile")
        ecg = find_test("ECG")
        cbc_test = find_test("Complete Blood Count")
        
        if all([lipid_test, ecg, cbc_test]):
            tests = [lipid_test, ecg, cbc_test]
            original = sum(t.price for t in tests)
            package_price = int(original * 0.75)
            
            pkg = LabPackage(
                id="pkg_003",
                name="Heart Health Package",
                description="Cardiac risk assessment with lipid profile and ECG",
                tests_included=[t.id for t in tests],
                original_price=original,
                package_price=package_price,
                savings=original - package_price,
                home_collection_available=False,
                home_collection_fee=0,
                category="Cardiac",
                popular=False
            )
            self.packages.append(pkg)
    
    def search_tests(self, query: str, filters: Optional[Dict] = None) -> List[LabTest]:
        """Search tests by name or category"""
        query_lower = query.lower()
        results = []
        
        # Extract base query without parentheses for better matching
        # "Complete Blood Count (CBC)" -> "Complete Blood Count"
        base_query = query_lower.split('(')[0].strip() if '(' in query_lower else query_lower
        
        # Also extract abbreviation if present
        # "Complete Blood Count (CBC)" -> "cbc"
        abbrev = None
        if '(' in query_lower and ')' in query_lower:
            abbrev = query_lower.split('(')[1].split(')')[0].strip()
        
        for test in self.tests:
            test_name_lower = test.name.lower()
            test_category_lower = test.category.lower()
            
            # Match if:
            # 1. Base query is in test name
            # 2. Abbreviation matches (e.g., "cbc" in "Complete Blood Count")
            # 3. Query is in category
            # 4. Original query matches
            if (base_query in test_name_lower or 
                query_lower in test_name_lower or 
                query_lower in test_category_lower or
                (abbrev and abbrev in test_name_lower.lower())):
                results.append(test)
        
        # Apply filters
        if filters:
            if "max_price" in filters:
                results = [t for t in results if t.price <= filters["max_price"]]
            if "home_collection" in filters and filters["home_collection"]:
                results = [t for t in results if t.home_collection_available]
            if "min_rating" in filters:
                results = [t for t in results if t.rating >= filters["min_rating"]]
        
        # Sort by popularity
        results.sort(key=lambda t: t.booking_count, reverse=True)
        return results
    
    def get_test(self, test_id: str) -> Optional[LabTest]:
        """Get test by ID"""
        return next((t for t in self.tests if t.id == test_id), None)
    
    def get_package(self, pkg_id: str) -> Optional[LabPackage]:
        """Get package by ID"""
        return next((p for p in self.packages if p.id == pkg_id), None)
    
    def recommend_package(self, selected_tests: List[str]) -> Optional[LabPackage]:
        """Recommend package if tests are part of one"""
        for pkg in self.packages:
            # Check if user's selected tests overlap with package tests
            overlap = set(selected_tests) & set(pkg.tests_included)
            if len(overlap) >= 2:  # If 2+ tests match, recommend package
                return pkg
        return None
    
    def get_available_slots(self, collection_type: str) -> List[LabSlot]:
        """Generate available time slots"""
        slots = []
        base_date = date.today()
        
        for day_offset in range(7):  # Next 7 days
            slot_date = base_date + timedelta(days=day_offset)
            
            # Morning slots
            for hour in [8, 9, 10, 11]:
                slot = LabSlot(
                    slot_id=f"slot_{slot_date.isoformat()}_{hour:02d}00",
                    date=slot_date.isoformat(),
                    time_range=f"{hour:02d}:00-{hour+1:02d}:00 AM",
                    collection_type=collection_type,
                    available=random.choice([True, True, True, False]),  # 75% availability
                    lab_name="CityCare Labs" if collection_type == "lab" else None,
                    lab_address="Sector 12, Pune" if collection_type == "lab" else None
                )
                slots.append(slot)
        
        return [s for s in slots if s.available]
