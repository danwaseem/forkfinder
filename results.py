import matplotlib.pyplot as plt

users  = [100, 200, 300, 400, 500]
avg_ms = [474, 386, 1544, 412, 5359]
p90_ms = [1044, 996, 5393, 1103, 21523]
errors = [33.33, 6.50, 0.00, 1.25, 0.67]

fig, ax1 = plt.subplots(figsize=(9, 5))
ax1.plot(users, avg_ms, marker='o', label='Avg response (ms)')
ax1.plot(users, p90_ms, marker='s', linestyle='--', label='p90 response (ms)')
ax1.set_xlabel('Concurrent Users')
ax1.set_ylabel('Response Time (ms)')
ax1.set_title('ForkFinder API — Response Time vs Concurrency (AWS EKS)')

ax2 = ax1.twinx()
ax2.bar(users, errors, alpha=0.25, label='Error %', width=25)
ax2.set_ylabel('Error Rate (%)')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.tight_layout()
plt.savefig('jmeter/results/response_time_vs_concurrency.png', dpi=150)
plt.show()