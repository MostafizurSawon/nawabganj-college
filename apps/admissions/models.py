from django.db import models

# Create your models here.

# Hsc and Degree
class Programs(models.Model):
    pro_name = models.CharField(max_length=20, null=True, blank=True)
    pro_status = models.CharField(max_length=15, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ],blank=True, null=True)
    pro_year = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.pro_name}"

# Degree
class DegreePrograms(models.Model):
    deg_name = models.CharField(max_length=20, null=True, blank=True)
    deg_status = models.CharField(max_length=15, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ],blank=True, null=True)
    deg_year = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.deg_name} ({self.deg_status}) - {self.deg_year}"

# Session (2024-25)      ***** Sesssion Wise Filter Full Menu (Except income expense)
class Session(models.Model):
    ses_name = models.CharField(max_length=20, null=True, blank=True)
    ses_status = models.CharField(max_length=15, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ],blank=True, null=True)

    def __str__(self):
        return f"{self.ses_name}"

# Degree Session
class DegreeSession(models.Model):
    ses_name = models.CharField(max_length=20, null=True, blank=True)
    ses_status = models.CharField(max_length=15, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ],blank=True, null=True)

    def __str__(self):
        return f"{self.ses_name}"

class Group(models.Model):
    group_name = models.CharField(max_length=20, choices=[
        ('science', 'Science'),
        ('arts', 'Humanities'),
        ('commerce', 'Business Studies'),
        ('Ba', 'BA'),
        ('Bss', 'BSS'),
        ('Bbs', 'BBS'),
        ('Bsc', 'BSC'),
    ], null=True, blank= True)

    def __str__(self):
        return f"{self.group_name}"

# All Subjects (Science, arts, commerce, Degree)
class Subjects(models.Model):
    sub_name = models.CharField(max_length=30, null=True, blank=True)
    group = models.CharField(max_length=20, choices=[
        ('science', 'Science'),
        ('arts', 'Humanities'),
        ('commerce', 'Business Studies'),
    ], null=True, blank= True)
    code = models.CharField(max_length=20, null=True, blank= True)
    sub_select = models.CharField(max_length=15, choices=[
        ('main', 'Main'),
        ('fourth', 'Fourth'),
        ('optional', 'Optional'),
        ('optional2', 'Optional2'),
        ('all', 'All'),
    ], blank=True, null=True)

    sub_status = models.CharField(max_length=15, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ],blank=True, null=True)

    def __str__(self):
        return f"{self.sub_name} ({self.code}) - {self.sub_select} - {self.group}"


# Honours/Degree subjects
class DegreeSubjects(models.Model):
    sub_name = models.CharField(max_length=30, null=True, blank=True)
    group = models.CharField(max_length=20, choices=[
            ('Ba', 'Ba'),
            ('Bss', 'Bss'),
            ('Bbs', 'Bbs'),
            ('Bsc', 'Bsc'),
        ], null=True, blank= True)
    code = models.CharField(max_length=20, null=True, blank= True)
    sub_status = models.CharField(max_length=15, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ],default='active', blank=True, null=True)

    def __str__(self):
        return f"{self.sub_name} ({self.code}) - {self.group}"



class Fee(models.Model):
    fee_session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='fee_session', verbose_name="Fee Session", null=True, blank=True)
    fee_program = models.ForeignKey(Programs, on_delete=models.CASCADE, related_name='fee_program', verbose_name="Fee Program", null=True, blank=True)    #Hsc
    fee_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='fee_group', verbose_name="Fee Group", null=True, blank=True)
    amount = models.PositiveIntegerField()

    class Meta:
        unique_together = ('fee_session', 'fee_program', 'fee_group')


    def __str__(self):
        return self.fee_group.group_name





# Admission Form
SSC_BOARDS = [
    ('Dhaka', 'Dhaka'),
    ('Chattogram', 'Chattogram'),
    ('Cumilla', 'Cumilla'),
    ('Rajshahi', 'Rajshahi'),
    ('Jashore', 'Jashore'),
    ('Sylhet', 'Sylhet'),
    ('Barishal', 'Barishal'),
    ('Dinajpur', 'Dinajpur'),
    ('Mymensingh', 'Mymensingh'),
    ('Madrasah', 'Madrasah'),
    ('Technical', 'Technical'),
]

class HscAdmissions(models.Model):
    add_program = models.ForeignKey(Programs, on_delete=models.CASCADE, null=True, blank=True)     # Hsc
    add_admission_group = models.CharField(
        max_length=20,
        choices=[
            ('science', 'Science'),
            ('arts', 'Humanities'),
            ('commerce', 'Business Studies'),
        ],
        null=True,
        blank=True
    )
    add_session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)   # session
    merit_position = models.IntegerField()
    add_name_bangla = models.CharField(max_length=100, null=True, blank=True)
    add_name = models.CharField(max_length=100)
    add_mobile = models.CharField(max_length=11, null=True, blank=True)

    # parent - conditional
    add_father_bangla = models.CharField(max_length=100, null=True, blank=True)
    add_father = models.CharField(max_length=100, null=True, blank=True)
    add_father_mobile = models.CharField(max_length=11, null=True, blank=True)

    add_mother_bangla = models.CharField(max_length=100, null=True, blank=True)
    add_mother = models.CharField(max_length=100, null=True, blank=True)
    add_mother_mobile = models.CharField(max_length=11, null=True, blank=True)

    add_parent_select = models.CharField(
        max_length=10,
        choices=[
            ('father', 'Father'),
            ('mother', 'Mother'),
            ('other', 'Other'),
        ],
        null=True,
        blank=True
    )

    add_parent = models.CharField(max_length=100, null=True, blank=True)
    add_parent_mobile = models.CharField(max_length=11, null=True, blank=True)
    add_parent_relation = models.CharField(max_length=20, null=True, blank=True)

    add_parent_service = models.CharField(max_length=30, null=True, blank=True)
    add_parent_income = models.IntegerField(null=True)

    add_parent_land_agri = models.CharField(max_length=30, null=True, blank=True)
    add_parent_land_nonagri = models.CharField(max_length=30, null=True, blank=True)


    # Address
    add_village = models.CharField(max_length=30, null=True, blank=True)
    add_post = models.CharField(max_length=30, null=True, blank=True)
    add_upojella = models.CharField(max_length=30, null=True, blank=True)
    add_distric= models.CharField(max_length=30, null=True, blank=True)

    add_address_same = models.BooleanField(default=False)

    add_village_per = models.CharField(max_length=30, null=True, blank=True)
    add_post_per = models.CharField(max_length=30, null=True, blank=True)
    add_upojella_per = models.CharField(max_length=30, null=True, blank=True)
    add_distric_per= models.CharField(max_length=30, null=True, blank=True)

    add_birthdate = models.DateField(null=True, blank=True) # ssc sonod Onujayi
    add_marital_status = models.CharField(max_length=10, choices=[
        ('Single', 'Single'),
        ('Married', 'Married'),
    ], null=True, blank=True)


    # Academic
    subjects = models.ManyToManyField('Subjects', blank=True, related_name='admitted_students')
    main_subject = models.ForeignKey('Subjects', on_delete=models.SET_NULL, null=True, blank=True, related_name='main_selected')
    fourth_subject = models.ForeignKey('Subjects', on_delete=models.SET_NULL, null=True, blank=True, related_name='fourth_selected')

    optional_subject = models.ForeignKey(
        'Subjects',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='optional_selected_1'
    )

    optional_subject_2 = models.ForeignKey(
        'Subjects',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='optional_selected_2'
    )



    add_ssc_roll = models.IntegerField(null=True)
    add_ssc_reg = models.IntegerField(null=True)
    add_ssc_session = models.CharField(max_length=30, null=True, blank=True)
    add_ssc_gpa = models.CharField(max_length=10, null=True, blank=True)
    add_ssc_group = models.CharField(max_length=10, choices=[
        ('science', 'Science'),
        ('arts', 'Humanities'),
        ('commerce', 'Business Studies'),
    ], null=True, blank=True)


    add_ssc_board = models.CharField(max_length=10, choices=SSC_BOARDS, null=True, blank=True)
    add_ssc_passyear = models.CharField(max_length=10, null=True, blank=True)

    add_payment_method = models.CharField(max_length=15, choices=[
        ('office', 'Office Cash'),
        ('bkash', 'Bkash'),
        ('rocket', 'Rocket'),
        ('nagad', 'Nagad'),
        ('bank', 'Bank'),
        ('others', 'Others'),
    ], null=True, blank=True)
    add_amount = models.PositiveIntegerField(null=True)      #ekhane admission fee auto boshbe. readonly forms.py a korbo
    add_trxid = models.CharField(max_length=50, null=True, blank=True)
    add_slip = models.CharField(max_length=150, null=True, blank=True)



    add_class_roll = models.IntegerField(null=True)
    add_hsc_year = models.CharField(max_length=10, choices=[
        ('1st', '1st'),
        ('2nd', '2nd')
    ], default='1st', null=True, blank=True)

    add_blood_group = models.CharField(max_length=3, choices=[
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ], null=True, blank=True)
    add_birth_certificate_no = models.CharField(max_length=50, null=True, blank=True)

    add_gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female')
    ])
    add_nationality = models.CharField(max_length=50)
    add_religion = models.CharField(max_length=20, choices=[
        ('Islam', 'Islam'),
        ('Hindu', 'Hindu'),
        ('Christian', 'Christian'),
        ('Buddhist', 'Buddhist'),
        ('Other', 'Other'),
    ])
    add_photo = models.ImageField(upload_to='admissions/hsc-science/%Y/%m/%d/')

    def __str__(self):
        return f"Name: {self.add_name} | Group: {self.add_admission_group} | Class Roll: {self.add_class_roll} | Session: {self.add_ssc_session}"







HSC_BOARDS = [
    ('Dhaka', 'Dhaka'),
    ('Chattogram', 'Chattogram'),
    ('Cumilla', 'Cumilla'),
    ('Rajshahi', 'Rajshahi'),
    ('Jashore', 'Jashore'),
    ('Sylhet', 'Sylhet'),
    ('Barishal', 'Barishal'),
    ('Dinajpur', 'Dinajpur'),
    ('Mymensingh', 'Mymensingh'),
    ('Madrasah', 'Madrasah'),
    ('Technical', 'Technical'),
]


class DegreeAdmission(models.Model):

    # Common Info
    add_name = models.CharField(max_length=100)
    add_name_bangla = models.CharField(max_length=100, null=True, blank=True)
    add_mobile = models.CharField(max_length=15)
    add_photo = models.ImageField(upload_to='degree/student_photos/', null=True, blank=True)
    add_birthdate = models.DateField(null=True, blank=True)
    add_blood_group = models.CharField(max_length=3, choices=[
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ], null=True, blank=True)
    add_birth_certificate_no = models.CharField(max_length=50, null=True, blank=True)

    add_gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female')
    ], null=True, blank=True)
    add_nationality = models.CharField(max_length=50, null=True, blank=True)
    add_religion = models.CharField(max_length=20, choices=[
        ('Islam', 'Islam'),
        ('Hindu', 'Hindu'),
        ('Christian', 'Christian'),
        ('Buddhist', 'Buddhist'),
        ('Other', 'Other'),
    ], null=True, blank=True)

    # SSC Info
    add_ssc_roll = models.CharField(max_length=20, null=True, blank=True)
    add_ssc_reg = models.CharField(max_length=20, null=True, blank=True)
    add_ssc_session = models.CharField(max_length=30, null=True, blank=True)
    add_ssc_gpa = models.CharField(max_length=10, null=True, blank=True)
    add_ssc_board = models.CharField(max_length=10, choices=SSC_BOARDS, null=True, blank=True)
    add_ssc_group = models.CharField(max_length=10, choices=[
        ('science', 'Science'),
        ('arts', 'Humanities'),
        ('commerce', 'Business Studies'),
    ], null=True, blank=True)
    add_ssc_passyear = models.CharField(max_length=10, null=True, blank=True)

    # parent - conditional
    add_father_bangla = models.CharField(max_length=100, null=True, blank=True)
    add_father = models.CharField(max_length=100, null=True, blank=True)
    add_father_mobile = models.CharField(max_length=11, null=True, blank=True)

    add_mother_bangla = models.CharField(max_length=100, null=True, blank=True)
    add_mother = models.CharField(max_length=100, null=True, blank=True)
    add_mother_mobile = models.CharField(max_length=11, null=True, blank=True)

    add_parent_select = models.CharField(
        max_length=10,
        choices=[
            ('father', 'Father'),
            ('mother', 'Mother'),
            ('other', 'Other'),
        ],
        null=True,
        blank=True
    )

    add_parent = models.CharField(max_length=100, null=True, blank=True)
    add_parent_mobile = models.CharField(max_length=11, null=True, blank=True)
    add_parent_relation = models.CharField(max_length=20, null=True, blank=True)

    add_parent_service = models.CharField(max_length=30, null=True, blank=True)
    add_parent_income = models.IntegerField(null=True)

    add_parent_land_agri = models.CharField(max_length=30, null=True, blank=True)
    add_parent_land_nonagri = models.CharField(max_length=30, null=True, blank=True)

    # HSC Info
    add_hsc_roll = models.CharField(max_length=20, null=True, blank=True)
    add_hsc_reg = models.CharField(max_length=20, null=True, blank=True)
    add_hsc_session = models.CharField(max_length=30, null=True, blank=True)
    add_hsc_gpa = models.CharField(max_length=10, null=True, blank=True)
    add_hsc_board = models.CharField(max_length=10, choices=HSC_BOARDS, null=True, blank=True)
    add_hsc_group = models.CharField(max_length=10, choices=[
        ('science', 'Science'),
        ('arts', 'Humanities'),
        ('commerce', 'Business Studies'),
    ], null=True, blank=True)
    add_hsc_passyear = models.CharField(max_length=10, null=True, blank=True)

    # Address
    add_village = models.CharField(max_length=30, null=True, blank=True)
    add_post = models.CharField(max_length=30, null=True, blank=True)
    add_upojella = models.CharField(max_length=30, null=True, blank=True)
    add_distric= models.CharField(max_length=30, null=True, blank=True)

    add_address_same = models.BooleanField(default=False)

    add_village_per = models.CharField(max_length=30, null=True, blank=True)
    add_post_per = models.CharField(max_length=30, null=True, blank=True)
    add_upojella_per = models.CharField(max_length=30, null=True, blank=True)
    add_distric_per= models.CharField(max_length=30, null=True, blank=True)

    add_birthdate = models.DateField(null=True, blank=True) # ssc sonod Onujayi
    add_marital_status = models.CharField(max_length=10, choices=[
        ('Single', 'Single'),
        ('Married', 'Married'),
    ], null=True, blank=True)

    # Grouping & Subjects
    add_program = models.ForeignKey(DegreePrograms, on_delete=models.CASCADE, null=True, blank=True)     # Ba, Bsc, Bss, Bbs
    add_admission_group = models.CharField(
        max_length=20,
        choices=[
            ('Ba', 'Ba'),
            ('Bss', 'Bss'),
            ('Bbs', 'Bbs'),
            ('Bsc', 'Bsc'),
        ],
        null=True,
        blank=True
    )
    add_session = models.ForeignKey('Session', on_delete=models.SET_NULL, null=True)
    subjects = models.ManyToManyField('DegreeSubjects', blank=True)
    main_subject = models.ForeignKey('DegreeSubjects', on_delete=models.SET_NULL, null=True, blank=True, related_name='degree_main_subject')

    add_class_roll = models.CharField(max_length=20, null=True, blank=True)
    merit_position = models.CharField(max_length=10, null=True, blank=True)

    add_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    add_payment_method = models.CharField(max_length=15, choices=[
        ('office', 'Office Cash'),
        ('bkash', 'Bkash'),
        ('rocket', 'Rocket'),
        ('nagad', 'Nagad'),
        ('bank', 'Bank'),
        ('others', 'Others'),
    ], null=True, blank=True)
    add_trxid = models.CharField(max_length=50, null=True, blank=True)
    add_slip = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.add_name
