from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

text = """
Operators of Camp Mystic, a century-old summer camp in the Texas Hill Country, said they lost 27 campers and counselors, confirming their worst fears after a wall of water slammed into cabins built along the edge of the Guadalupe River.

“We have been in communication with local and state authorities who are tirelessly deploying extensive resources to search for our missing girls,” the camp said in a statement. Authorities later said that 10 girls and a counselor from the camp remain missing.
"""

summary = summarizer(text, max_length=60, min_length=10, do_sample=False)
print("Summary:", summary[0]['summary_text'])
