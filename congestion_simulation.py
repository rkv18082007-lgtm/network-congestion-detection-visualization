import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Network topology
positions = {
    "h1": (0, 1),
    "s1": (1, 1),
    "s2": (2, 1.6),
    "s3": (2, 0.4),
    "s4": (3, 1),
    "h2": (4, 1)
}

links = [
    ("h1", "s1"),
    ("s1", "s2"),
    ("s2", "s4"),
    ("s1", "s3"),
    ("s3", "s4"),
    ("s4", "h2")
]

UPPER_ROUTE = ["h1", "s1", "s2", "s4", "h2"]
LOWER_ROUTE = ["h1", "s1", "s3", "s4", "h2"]

QUEUE_LIMIT = 12
SERVICE_CAPACITY = 7

queue_length = 0
total_packets = 0
dropped_packets = 0
tick = 0
packets = []

history = {
    "time": [],
    "traffic": [],
    "queue": [],
    "drops": []
}

fig = plt.figure(figsize=(13, 9))
layout = fig.add_gridspec(2, 2, height_ratios=[1.2, 1])

ax_top = fig.add_subplot(layout[0, :])
ax_traffic = fig.add_subplot(layout[1, 0])
ax_queue = fig.add_subplot(layout[1, 1])
ax_drops = ax_queue.twinx()


def update(frame):
    global queue_length, total_packets, dropped_packets, tick

    tick += 1

    # Alternate between normal and heavy traffic
    phase = tick % 100

    if 30 <= phase < 70:
        arrivals = random.randint(14, 18)
    else:
        arrivals = random.randint(3, 7)

    total_packets += arrivals

    # Model the queue at S1
    available_space = QUEUE_LIMIT - queue_length
    accepted = min(arrivals, available_space)
    newly_dropped = arrivals - accepted

    queue_length += accepted
    dropped_packets += newly_dropped

    # Detect congestion
    congested = (
        arrivals > SERVICE_CAPACITY
        or queue_length >= 8
        or newly_dropped > 0
    )

    # Process queued packets
    served = min(queue_length, SERVICE_CAPACITY)
    queue_length -= served

    # Create new moving packets continuously
    visual_count = min(arrivals, 5)
    visual_drops = min(newly_dropped, visual_count)

    for i in range(visual_count):
        path = random.choice(
            [UPPER_ROUTE, LOWER_ROUTE]
        ).copy()

        packets.append({
            "path": path,
            "progress": 0.0,
            "speed": 0.018 if congested else 0.045,
            "dropped": i < visual_drops
        })

    # Move packets every animation frame
    for packet in packets[:]:
        packet["progress"] += packet["speed"]

        # Dropped packets disappear near S1
        if packet["dropped"] and packet["progress"] >= 0.24:
            packets.remove(packet)

        # Successful packets disappear after reaching H2
        elif packet["progress"] >= 1.0:
            packets.remove(packet)

    # Store graph data
    history["time"].append(tick)
    history["traffic"].append(arrivals)
    history["queue"].append(queue_length)
    history["drops"].append(dropped_packets)

    for key in history:
        history[key] = history[key][-100:]

    # Draw network links
    ax_top.clear()

    for a, b in links:
        x1, y1 = positions[a]
        x2, y2 = positions[b]

        if congested and (a == "s1" or b == "s1"):
            link_color = "red"
            link_width = 4
        else:
            link_color = "gray"
            link_width = 2

        ax_top.plot(
            [x1, x2],
            [y1, y2],
            color=link_color,
            linewidth=link_width,
            zorder=1
        )

    # Draw hosts and switches
    for name, (x, y) in positions.items():
        if name == "s1":
            node_color = "red" if congested else "#BDECC8"
        elif name.startswith("h"):
            node_color = "#B8E0FF"
        else:
            node_color = "#BDECC8"

        text_color = (
            "white" if name == "s1" and congested else "black"
        )

        ax_top.scatter(
            x, y,
            s=1100,
            color=node_color,
            edgecolor="black",
            linewidth=1.5,
            zorder=3
        )

        ax_top.text(
            x, y, name,
            ha="center",
            va="center",
            color=text_color,
            fontweight="bold",
            zorder=4
        )

    # Draw moving packets
    for packet in packets:
        path = packet["path"]

        progress = packet["progress"] * (len(path) - 1)
        segment = min(int(progress), len(path) - 2)
        fraction = progress - segment

        x1, y1 = positions[path[segment]]
        x2, y2 = positions[path[segment + 1]]

        px = x1 + fraction * (x2 - x1)
        py = y1 + fraction * (y2 - y1)

        if packet["dropped"]:
            packet_color = "black"
        elif congested:
            packet_color = "orange"
        else:
            packet_color = "green"

        ax_top.scatter(
            px, py,
            s=45,
            color=packet_color,
            edgecolor="black",
            linewidth=0.4,
            zorder=5
        )

    # Status message
    if congested:
        status = "CONGESTION DETECTED AT S1!"
        status_color = "red"
        behavior = "Orange: slowed | Lower route: rerouting | Black: dropped"
    else:
        status = "NORMAL TRAFFIC"
        status_color = "green"
        behavior = "Green dots: moving packets"

    ax_top.set_title(
        "Network Congestion Detection Simulation",
        fontweight="bold"
    )

    ax_top.text(
        2, 2.0,
        status,
        ha="center",
        color=status_color,
        fontweight="bold",
        fontsize=12
    )

    ax_top.text(
        2, 1.82,
        behavior,
        ha="center",
        fontsize=9
    )

    ax_top.text(
        2, -0.05,
        f"Incoming: {arrivals} | Queue: {queue_length}/{QUEUE_LIMIT} | "
        f"New drops: {newly_dropped} | Total drops: {dropped_packets}",
        ha="center",
        fontweight="bold"
    )

    ax_top.set_xlim(-0.5, 4.5)
    ax_top.set_ylim(-0.3, 2.25)
    ax_top.axis("off")

    # Incoming traffic graph
    ax_traffic.clear()

    ax_traffic.plot(
        history["time"],
        history["traffic"],
        color="blue"
    )

    ax_traffic.set_title("Incoming Traffic per Tick")
    ax_traffic.set_xlabel("Simulation Tick")
    ax_traffic.set_ylabel("Incoming Packets")
    ax_traffic.grid(True, alpha=0.3)

    # Queue length and cumulative packet drops
    ax_queue.clear()
    ax_drops.clear()

    ax_queue.plot(
        history["time"],
        history["queue"],
        color="orange"
    )

    ax_queue.axhline(
        QUEUE_LIMIT,
        color="red",
        linestyle="--"
    )

    ax_queue.set_title("S1 Queue Length and Packet Drops")
    ax_queue.set_xlabel("Simulation Tick")
    ax_queue.set_ylabel("Queue Length", color="orange")
    ax_queue.set_ylim(0, QUEUE_LIMIT + 2)
    ax_queue.grid(True, alpha=0.3)

    ax_drops.plot(
        history["time"],
        history["drops"],
        color="crimson"
    )

    ax_drops.set_ylabel(
        "Cumulative Packet Drops",
        color="crimson"
    )

    fig.tight_layout()


animation = FuncAnimation(
    fig,
    update,
    interval=100,
    cache_frame_data=False
)

plt.show()

print("Simulation closed.")
print("Total packets generated:", total_packets)
print("Total packets dropped:", dropped_packets)

if total_packets:
    print(
        "Packet drop percentage:",
        round(100 * dropped_packets / total_packets, 2),
        "%"
    )