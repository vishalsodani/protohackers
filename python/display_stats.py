import pstats

with open("profilingStats_4.txt", "w") as f:
    ps = pstats.Stats("profile_job_4", stream=f)
    ps.sort_stats('cumulative')
    ps.print_stats()