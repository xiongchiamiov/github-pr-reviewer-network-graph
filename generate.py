#!/usr/bin/env python3

import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from github import Github

gh = Github(os.environ['GITHUB_TOKEN'])

repos = sys.argv[1:]
counter = defaultdict(Counter)
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
            counter[pr.user.name][reviewer] += 1

print(counter)
print(i)
print(all_users)
