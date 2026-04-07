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

file1 = load_json("/home/michael/Documents/software/fray-benchmark/tmp-out-random/interleaving_sequences.json")
file2 = load_json("/home/michael/Documents/software/fray-benchmark/tmp-out-pos/interleaving_sequences.json")
file3 = load_json("/home/michael/Documents/software/fray-benchmark/tmp-out-llm/interleaving_sequences.json")

x1, y1 = cumulative_dense(file1)
x2, y2 = cumulative_dense(file2)
x3, y3 = cumulative_dense(file3)

plt.figure(figsize=(10, 6))
plt.plot(x1, y1, label="random")
plt.plot(x2, y2, label="pos")
plt.plot(x3, y3, label="llm")

plt.xlabel("numberOfIteration")
plt.ylabel("number of interruptPoints sets with firstIteration <= x")
plt.title("Cumulative number of interruptPoints sets by iteration")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("plot.png", dpi=200)
plt.close()
