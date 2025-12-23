import random
from typing import List, Dict, Optional
from .models import LabTest, LabPackage, LabSlot
from datetime import date, timedelta

class LabTestDatabase:
    def __init__(self):
        self.tests: List[LabTest] = []
        self.packages: List[LabPackage] = []
        self._seed_data()
    
    def _seed_data(self):
        """Generate mock lab tests and packages"""
        
        # Blood Tests
        blood_tests = [
            ("CBC", "Complete Blood Count", ["Hemoglobin", "WBC", "Platelets"], 25, 500, True, False, "No special preparation"),
            ("Lipid Profile", "Cholesterol & Triglycerides", ["Total Cholesterol", "HDL", "LDL", "Triglycerides"], 8, 800, True, True, "12-14 hours fasting required"),
            ("Thyroid Profile", "TSH, T3, T4", ["TSH", "T3 Total", "T4 Total"], 3, 700, True, False, "Can be done anytime"),
            ("HbA1c", "Diabetes Monitoring", ["Glycated Hemoglobin"], 1, 600, True, False, "No fasting needed"),
            ("Liver Function Test (LFT)", "Liver Enzymes", ["SGOT", "SGPT", "Bilirubin", "Albumin"], 12, 900, True, True, "8-12 hours fasting"),
            ("Kidney Function Test (KFT)", "Renal Profile", ["Creatinine", "BUN", "Uric Acid"], 8, 850, True, True, "8 hours fasting"),
            ("Vitamin D", "Vitamin D (25-OH)", ["25-Hydroxyvitamin D"], 1, 1200, True, False, "No preparation needed"),
            ("Vitamin B12", "B12 Levels", ["Cobalamin"], 1, 900, True, False, "No preparation"),
            ("Iron Studies", "Serum Iron Profile", ["Serum Iron", "TIBC", "Ferritin"], 3, 1100, True, True, "Morning sample preferred"),
            ("ESR", "Erythrocyte Sedimentation Rate", ["ESR"], 1, 200, True, False, "No preparation"),
            ("CRP", "C-Reactive Protein", ["CRP"], 1, 500, True, False, "No preparation"),
            ("Fasting Blood Sugar", "FBS", ["Glucose"], 1, 150, True, True, "8-12 hours fasting required"),
            ("PPBS", "Post-Prandial Blood Sugar", ["Glucose"], 1, 150, False, False, "Test after 2 hours of meal"),
        ]
        
        for idx, (name, full_name, params, param_count, price, home, fasting, prep) in enumerate(blood_tests):
            test = LabTest(
                id=f"test_blood_{idx+1:03d}",
                name=full_name,
                category="Blood Tests",
                price=price,
                home_collection_available=home,
                home_collection_fee=50 if home else 0,
                sample_type="Blood",
                fasting_required=fasting,
                preparation_instructions=prep,
                turnaround_time=random.choice(["24 hours", "Same day", "48 hours"]),
                parameters_count=param_count,
                rating=round(random.uniform(4.0, 4.9), 1),
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
        
        for test in self.tests:
            if (query_lower in test.name.lower() or 
                query_lower in test.category.lower()):
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
