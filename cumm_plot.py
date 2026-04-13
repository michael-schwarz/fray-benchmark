import json
import matplotlib.pyplot as plt

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def cumulative_dense(data):
    max_iter = max((row["firstIteration"] for row in data), default=0)
    hits = [0] * (max_iter + 1)

    for row in data:
        hits[row["firstIteration"]] += 1

    xs = list(range(max_iter + 1))
    ys = []
    running = 0
    for x in xs:
        running += hits[x]
        ys.append(running)

    return xs, ys

file1 = load_json("/home/michael/Documents/software/fray-benchmark/2g2bt/random-long/interleaving_sequences.json")
file2 = load_json("/home/michael/Documents/software/fray-benchmark/2g2bt/pos-long/interleaving_sequences.json")
file3 = load_json("/home/michael/Documents/software/fray-benchmark/2g2bt/llm-long/interleaving_sequences.json")
file4 = load_json("/home/michael/Documents/software/fray-benchmark/2g2bt/llm-long-1/interleaving_sequences.json")
file5 = load_json("/home/michael/Documents/software/fray-benchmark/2g2bt/llm-long-2/interleaving_sequences.json")
file6 = load_json("/home/michael/Documents/software/fray-benchmark/2g2bt/llm-long-4/interleaving_sequences.json")

x1, y1 = cumulative_dense(file1)
x2, y2 = cumulative_dense(file2)
x3, y3 = cumulative_dense(file3)
x4, y4 = cumulative_dense(file4)
x5, y5 = cumulative_dense(file5)
x6, y6 = cumulative_dense(file6)

plt.figure(figsize=(10, 6))
plt.plot(x1, y1, label="random")
plt.plot(x2, y2, label="pos")
plt.plot(x3, y3, label="llm-3")
plt.plot(x4, y4, label="llm-1")
plt.plot(x5, y5, label="llm-2")
plt.plot(x6, y6, label="llm-4")

# Bold vertical reference lines
plt.axvline(x=200, linewidth=2.5, linestyle="--", color="black")
plt.axvline(x=600, linewidth=2.5, linestyle="--", color="black")
plt.axvline(x=1400, linewidth=2.5, linestyle="--", color="black")
plt.axvline(x=3000, linewidth=2.5, linestyle="--", color="black")



plt.xlabel("numberOfIteration")
plt.ylabel("number of interruptPoints sets with firstIteration <= x")
plt.title("Cumulative number of interruptPoints sets by iteration")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("plot-long.png", dpi=200)
plt.close()
