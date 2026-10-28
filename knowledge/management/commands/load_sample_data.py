"""Load a few SAMPLE FAQs so the team can test the chatbot right away.

Usage:  python manage.py load_sample_data
These are placeholders. Replace them with the university's official
information collected in Sprint 1 before any real student uses the bot.
"""
from django.core.management.base import BaseCommand

from knowledge.models import Category, FAQ

SAMPLE_NOTE_EN = " [SAMPLE – replace with official data]"
SAMPLE_NOTE_KM = " [ឧទាហរណ៍ – សូមជំនួសដោយព័ត៌មានផ្លូវការ]"

CATEGORIES = [
    ("Courses", "មុខវិជ្ជា"),
    ("Fees", "ថ្លៃសិក្សា"),
    ("Schedules", "កាលវិភាគ"),
    ("Services", "សេវាកម្ម"),
    ("Admissions", "ការចុះឈ្មោះចូលរៀន"),
]

FAQS = [
    ("Fees", "en", "Where can I pay my tuition fees?",
     "You can pay tuition fees at the Finance Office on the ground floor, Monday to Friday, 8:00–17:00, "
     "or by bank transfer using your student ID as the reference."),
    ("Fees", "en", "What is the deadline for paying tuition fees?",
     "Tuition fees must be paid before the first day of each semester. A late fee applies after the deadline."),
    ("Schedules", "en", "Where can I find my class schedule?",
     "Class schedules are posted on the faculty notice board and on the university website under Students > Schedules."),
    ("Schedules", "en", "When are the final exams?",
     "Final exams take place in the last two weeks of each semester. The exact timetable is published one month before."),
    ("Courses", "en", "How do I know which courses I need for my major?",
     "Each major has a study plan listing required courses by year. Ask your faculty office or check the study plan on the website."),
    ("Services", "en", "What are the library opening hours?",
     "The library is open Monday to Saturday, 7:30–20:00. Bring your student ID card to borrow books."),
    ("Services", "en", "How do I replace a lost student ID card?",
     "Go to the Student Affairs Office with a photo and pay the replacement fee. The new card is ready in 3 working days."),
    ("Admissions", "en", "What documents do I need to apply?",
     "You need your high school certificate (or provisional certificate), national ID card, 4 photos (4x6) and the completed application form."),
    ("Fees", "km", "តើខ្ញុំអាចបង់ថ្លៃសិក្សានៅឯណា?",
     "អ្នកអាចបង់ថ្លៃសិក្សានៅការិយាល័យហិរញ្ញវត្ថុ ចាប់ពីថ្ងៃច័ន្ទ ដល់ថ្ងៃសុក្រ ម៉ោង ៨:០០ ដល់ ១៧:០០។"),
    ("Services", "km", "តើបណ្ណាល័យបើកម៉ោងប៉ុន្មាន?",
     "បណ្ណាល័យបើកពីថ្ងៃច័ន្ទ ដល់ថ្ងៃសៅរ៍ ម៉ោង ៧:៣០ ដល់ ២០:០០។"),
]


class Command(BaseCommand):
    help = "Load sample categories and FAQs for development and demos."

    def handle(self, *args, **options):
        categories = {}
        for name, name_km in CATEGORIES:
            categories[name], _ = Category.objects.get_or_create(name=name, defaults={"name_km": name_km})

        created = 0
        for cat, lang, question, answer in FAQS:
            note = SAMPLE_NOTE_KM if lang == "km" else SAMPLE_NOTE_EN
            # Saving an FAQ triggers indexing automatically (signals.py)
            _, was_created = FAQ.objects.get_or_create(
                question=question,
                defaults={"category": categories[cat], "language": lang, "answer": answer + note},
            )
            created += was_created
        self.stdout.write(self.style.SUCCESS(f"Loaded {created} new sample FAQ(s)."))
