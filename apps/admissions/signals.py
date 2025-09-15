# admissions/signals.py
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import HscAdmissions, Subjects

def bump_counts_for_subjects(subjects, delta):
    """নির্দিষ্ট subject তালিকার used_count বাড়ায়/কমায়।"""
    for sub in subjects:
        if sub:
            sub.used_count = (sub.used_count or 0) + delta
            if sub.used_count < 0:
                sub.used_count = 0
            sub.save(update_fields=['used_count'])

@receiver(pre_save, sender=HscAdmissions)
def admission_pre_save(sender, instance, **kwargs):
    """
    সংরক্ষণ করার আগে পুরোনো সাবজেক্টগুলোর একটি তালিকা instance._old_subjects এ রেখে দিই,
    যাতে post_save এ আমরা পার্থক্য বের করতে পারি।
    """
    if instance.pk:
        old = sender.objects.get(pk=instance.pk)
        instance._old_subjects = [
            old.main_subject,
            old.fourth_subject,
            old.optional_subject,
            old.optional_subject_2,
        ]
    else:
        instance._old_subjects = []

@receiver(post_save, sender=HscAdmissions)
def admission_saved(sender, instance, created, **kwargs):
    """
    নতুন রেকর্ড তৈরি হলে সব নির্বাচিত subject এর used_count এক ধাপ বাড়াই।
    আর আপডেট হলে পুরোনো এবং নতুন subject তালিকা মিলিয়ে যা পরিবর্তন হয়েছে
    সেটির উপর ভিত্তি করে used_count সমন্বয় করি।
    """
    new_subjects = [
        instance.main_subject,
        instance.fourth_subject,
        instance.optional_subject,
        instance.optional_subject_2,
    ]

    if created:
        # নতুন আবেদন: চারটি সাবজেক্ট ফিল্ডে যা আছে তা ব্যবহার গণনায় যোগ করি
        bump_counts_for_subjects(new_subjects, +1)
    else:
        old_subjects = getattr(instance, '_old_subjects', []) or []

        # পুরোনো তালিকায় ছিল কিন্তু নতুন তালিকায় নেই – তাদের used_count কমাই
        for sub in old_subjects:
            if sub and sub not in new_subjects:
                sub.used_count = (sub.used_count or 0) - 1
                if sub.used_count < 0:
                    sub.used_count = 0
                sub.save(update_fields=['used_count'])

        # নতুন তালিকায় আছে কিন্তু পুরোনো তালিকায় ছিল না – তাদের used_count বাড়াই
        for sub in new_subjects:
            if sub and sub not in old_subjects:
                sub.used_count = (sub.used_count or 0) + 1
                sub.save(update_fields=['used_count'])

@receiver(post_delete, sender=HscAdmissions)
def admission_deleted(sender, instance, **kwargs):
    """
    রেকর্ড মুছে ফেলার সময় বর্তমান subject গুলোর used_count এক ধাপ কমাই।
    """
    old_subjects = [
        instance.main_subject,
        instance.fourth_subject,
        instance.optional_subject,
        instance.optional_subject_2,
    ]
    bump_counts_for_subjects(old_subjects, -1)
