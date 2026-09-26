"""
retrieval.py
Retrieves from the knowledge base (the data/ folder) the information needed
to assess a student's text for a specific task.
- Always included: the Cambridge rubric and the institutional criteria.
- Retrieved per task: the task sheet, its extra vocabulary (if any) and the benchmark samples of that task.
"""
 
from pathlib import Path
 
# Path to the data/ folder, next to this file
DATA_DIR = Path(__file__).parent / "data"
 
 
def read_file(path):
    """Read a text file and return its content as a string."""
    return path.read_text(encoding="utf-8")
 


def get_field(text, field_name):
    """
    Find a line like 'Task: cadet_routine' and return the value after the colon.
    Returns None if the field is not found. it reads a line like Task: cadet_routine and returns what comes after the colon. 
    That's how load_samples knows which samples belong to which task
    """
    for line in text.splitlines():
        if line.startswith(field_name + ":"):
            return line.split(":", 1)[1].strip()
    return None
 
 
def load_rubric():
    """The official Cambridge rubric (used for every task)."""
    return read_file(DATA_DIR / "rubric_cambridge_a2.md")
 
 
def load_criteria():
    """The institutional criteria (used for every task)."""
    return read_file(DATA_DIR / "criteria.md")
 

def list_tasks():
    """Return the ids of all available tasks, based on the files in data/tasks/."""
    tasks = []
    for path in sorted((DATA_DIR / "tasks").glob("*.md")):
        tasks.append(path.stem)
    return tasks
 
 
def load_task(task_id):
    """Load the task sheet for one task."""
    path = DATA_DIR / "tasks" / f"{task_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"Task '{task_id}' not found: {path}")
    return read_file(path)
 
 
def load_extra_vocabulary(task_text):
    """
    If the task sheet has a line like 'Extra vocabulary: military.md',
    load that file from data/vocabulary/. Otherwise return an empty string.
    """
    file_name = get_field(task_text, "Extra vocabulary")
    if file_name is None:
        return ""
    return read_file(DATA_DIR / "vocabulary" / file_name)
 
 
def load_samples(task_id):
    """Load only the benchmark samples whose 'Task:' line matches this task."""
    samples = []
    for path in sorted((DATA_DIR / "samples").glob("*.md")):
        text = read_file(path)
        if get_field(text, "Task") == task_id:
            samples.append(text)
    return samples
 
 
def retrieve_context(task_id):
    """Collect everything the LLM needs to assess a text for this task."""
    task = load_task(task_id)
    return {
        "rubric": load_rubric(),
        "criteria": load_criteria(),
        "task": task,
        "vocabulary": load_extra_vocabulary(task),
        "samples": load_samples(task_id),
    }
 
 
# Quick test: run "python retrieval.py" in the terminal
if __name__ == "__main__":
    print("Available tasks:", list_tasks())
 
    for task_id in list_tasks():
        context = retrieve_context(task_id)
        print(f"\n=== {task_id} ===")
        print("Benchmark samples found:", len(context["samples"]))
        print("Extra vocabulary loaded:", "yes" if context["vocabulary"] else "no")
        for sample in context["samples"]:
            print("  -", get_field(sample, "Scores"))
