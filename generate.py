#!/usr/bin/env python3

import os
import sys
from collections import Counter
from datetime import datetime, timedelta

from github import Github
from jinja2 import Environment, FileSystemLoader

gh = Github(os.environ['GITHUB_TOKEN'])

repos = sys.argv[1:]
counter = Counter()
all_users = set()

now = datetime.now()
time_limit = timedelta(days=(365/4))

i = 0
for repo_name in repos:
    repo = gh.get_repo(repo_name)
    for pr in repo.get_pulls(state='all', sort='updated', direction='desc'):
        # Limit to only "recent" activity so a) it's more relevant and b) it
        # doesn't take forever to run.
        if (now - pr.updated_at) > time_limit:
            print('stopping at {}'.format(pr.updated_at))
            break

        i += 1
        print(pr.number)
        # People can submit multiple reviews of a PR, so we need to
        # de-duplicate them.
        reviewers = set()

        for review in pr.get_reviews():
            if review.user.name == pr.user.name:
                # It's not interesting to know when people submit self-reviews.
                continue
            if review.user.name is None:
                # I think this happens when a bot does a review.  I also don't
                # care about that.
                continue

            reviewers.add(review.user.name)

        all_users.add(pr.user.name)
        all_users.update(reviewers)

        for reviewer in reviewers:
            # We need to merge together A->B and B->A.  This is a pain to do
            # later, so we'll pull them together into a single hash key right
            # now.
            key = tuple(sorted((pr.user.name, reviewer)))
            counter[key] += 1

print(counter)
print(i)
print(all_users)

users = {}
i = 0
for user in all_users:
    users[user] = i
    i += 1

edges = []
for people, count in counter.items():
    edges.append({
        'from': users[people[0]],
        'to': users[people[1]],
        'value': count,
    })

env = Environment(loader=FileSystemLoader('.'))
with open('index.html', 'w') as f:
    f.write(env.get_template('template.html').render(users=users, edges=edges))
