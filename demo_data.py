"""
Synthetic sample data for DigitalTrace demo mode.

Everything here is fictional: the profiles, job titles, and URLs are invented
placeholders shaped like SerpApi organic results. They are NOT real search
results and do not describe any real person. Demo mode feeds this data through
the real evidence engine, clustering, and scoring code so the pipeline can be
demonstrated without exposing anyone's actual online identity.
"""


def get_demo_results(name):
    slug = name.lower().strip().replace(" ", "-")
    underscore = name.lower().strip().replace(" ", "_")

    return [
        {
            "title": f"{name} - Financial Analyst at Northwind Demo Corp",
            "link": f"https://www.linkedin.com/in/demo-{slug}-fin",
            "snippet": f"{name}. Financial Analyst. Austin, USA.",
            "query_source": "LinkedIn",
        },
        {
            "title": f"{name} - Software Engineer at Contoso Demo Labs",
            "link": f"https://in.linkedin.com/in/demo-{slug}-eng",
            "snippet": f"{name}. Software Engineer. Bangalore, India.",
            "query_source": "LinkedIn",
        },
        {
            "title": f"{name} - Student at Demo Institute of Technology",
            "link": f"https://in.linkedin.com/in/demo-{slug}-4471829",
            "snippet": f"{name}. Student. Delhi, India.",
            "query_source": "LinkedIn",
        },
        {
            "title": f"{name} (@demo_{underscore}_2231) • Instagram photos and videos",
            "link": f"https://www.instagram.com/demo_{underscore}_2231/",
            "snippet": f"{name}. Singer | Mumbai.",
            "query_source": "Instagram",
        },
        {
            "title": f"{name}",
            "link": f"https://www.facebook.com/demo.{slug}.1/",
            "snippet": f"{name} is on Facebook.",
            "query_source": "Facebook",
        },
        {
            "title": f"Why {name} inspired our whole team",
            "link": f"https://www.linkedin.com/posts/demo-author_{slug}-activity-0000000000",
            "snippet": f"A post by someone else praising {name}'s leadership.",
            "query_source": "News/Articles",
        },
    ]