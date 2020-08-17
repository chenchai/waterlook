from django.core.management.base import BaseCommand, CommandError
from catalog.models import Course
from django.db.utils import DataError, IntegrityError
import requests
import environ
import json

# Environment should already be read in settings.py
env = environ.Env()

class Command(BaseCommand):
    help = "updates course list in database from API"
    
    def handle(self, *args, **kwargs):
        newCourses = 0

        # First, get the list of all the academic terms.
        # V3 API contains this list.
        response = requests.get(f"https://openapi.data.uwaterloo.ca/v3/Terms",
            headers={
                'Accept':'application/json',
                'x-api-key': env("OPENDATA_V3_KEY")})
        
        terms = response.json()
        for term in terms:
            termCode = term['code']
            print("Term: " + termCode)
            
            key = env("OPENDATA_V2_KEY")

            # API call to get courses for this term.
            response = requests.get(
                f"https://api.uwaterloo.ca/v2/terms/{termCode}/courses.json?key={key}")
            
            courses = response.json()['data']
            
            # Update existing courses as an in-memory dictionary 
            # for fast comparisons
            existingCourses = list(Course.objects.all())
            existingDict = {}

            # https://stackoverflow.com/questions/8550912/dictionary-of-dictionaries-in-python
            for existing in existingCourses:
                existingDict.setdefault(existing.subject, {})[existing.code] = True
        
            for course in courses:
                s = course['subject']
                c = str(course['catalog_number'])

                
                # Check if a course already exists in database;
                # if not, insert it into the database.
                if existingDict.get(s, {}).get(c, False) == True:
                    ""
                    # print("Course already exists; skipping insert.")
                else:
                    print("Course found: " + s + " " + c)
                    try:
                        record = Course(subject=s, code=c)
                        record.save()
                        
                        newCourses += 1

                    except IntegrityError as e:
                        print("Error inserting course: " + str(e))
                    
                    except DataError as e:
                        print("Error inserting course: " + str(e))
        
        print("Done! Found " + str(newCourses) + " new courses (searched " + str(len(terms)) + " terms)")
    