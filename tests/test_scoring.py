import yaml
from jobagent.models import Job
from jobagent.scoring import keyword_score, rank

CFG = yaml.safe_load(open("config.yaml"))
CFG["notify"]["use_llm"] = False


def J(title, loc, desc="", remote=False, jt=""):
    return Job(id=title + loc, title=title, company="X", location=loc, url="http://x", description=desc, remote=remote, job_type=jt)


def test_good_local_intern_scores_high():
    j = J("Data Science Intern", "Kolkata, West Bengal", "Python pandas SQL machine learning streamlit", jt="internship")
    assert keyword_score(j, CFG) >= 70


def test_senior_excluded():
    assert keyword_score(J("Senior Data Engineer", "Kolkata", "python sql"), CFG) == 0


def test_us_only_remote_rejected():
    assert keyword_score(J("Python Developer Intern", "USA Only", "python", remote=True), CFG) == 0


def test_worldwide_remote_ok():
    assert keyword_score(J("Junior Data Analyst", "Worldwide", "python sql excel", remote=True), CFG) > 40


def test_other_country_rejected():
    assert keyword_score(J("Data Analyst Intern", "London, UK", "python sql"), CFG) == 0


def test_rank_filters_threshold_and_sorts():
    jobs = [J("Data Analyst Intern", "Kolkata", "python sql excel power bi", jt="internship"),
            J("Office Assistant", "Kolkata", "filing")]
    out = rank(jobs, CFG)
    assert len(out) == 1 and out[0].title.startswith("Data Analyst")
