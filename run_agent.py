from app.coordinator import DroneOpsCoordinator


def handle_command(coordinator: DroneOpsCoordinator, message: str) -> str:
    text = message.lower().strip()

    if text == "find pilots":
        return "\n".join(
            f"{p.pilot_id}: {p.name} | {p.status} | {p.current_location}" for p in coordinator.pilots
        )
    if text == "find drones":
        return "\n".join(
            f"{d.drone_id}: {d.model} | {d.status} | {d.location}" for d in coordinator.drones
        )
    if text == "detect conflicts":
        conflicts = coordinator.detect_conflicts()
        return "No conflicts." if not conflicts else "\n".join(conflicts)
    if text.startswith("assign "):
        return coordinator.assign_project(text.split()[1].upper())
    if text.startswith("urgent reassign "):
        return coordinator.urgent_reassignment(text.split()[2].upper())

    return "Commands: find pilots | find drones | detect conflicts | assign <ID> | urgent reassign <ID> | quit"


def main():
    coordinator = DroneOpsCoordinator()
    print("Drone Operations Coordinator Agent (CLI)")
    print("Type 'quit' to exit.")
    while True:
        msg = input("\n> ").strip()
        if msg.lower() in {"quit", "exit"}:
            print("Goodbye")
            break
        coordinator.refresh()
        print(handle_command(coordinator, msg))


if __name__ == "__main__":
    main()
