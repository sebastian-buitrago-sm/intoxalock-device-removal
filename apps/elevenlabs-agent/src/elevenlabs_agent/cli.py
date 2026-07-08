import argparse

from elevenlabs_agent.calling.outbound import place_call
from elevenlabs_agent.client import build_client
from elevenlabs_agent.config import load_settings
from elevenlabs_agent.sync.agent_sync import create_agent, sync_agent


def _create_agent(env: str) -> None:
    settings = load_settings(env)
    client = build_client(settings)
    agent = create_agent(client, settings)
    print(f"[{env}] agent created: {agent.agent_id}")
    print(f'Add agent_id = "{agent.agent_id}" to config/{env}.toml, then use sync-agent.')


def _sync_agent(env: str) -> None:
    settings = load_settings(env)
    client = build_client(settings)
    agent = sync_agent(client, settings)
    print(f"[{env}] agent synced: {agent.agent_id} (version {agent.version_id})")


def _call(
    *,
    env: str,
    to_number: str,
    user_id: str,
    slot_1: str,
    slot_2: str,
    vehicle_make: str,
    vehicle_model: str,
    vehicle_year: str,
) -> None:
    settings = load_settings(env)
    client = build_client(settings)
    outcome = place_call(
        client,
        settings,
        to_number=to_number,
        dynamic_variables={
            "user_id": user_id,
            "user_scheduled_slot_1": slot_1,
            "user_scheduled_slot_2": slot_2,
            "user_vehicle_make": vehicle_make,
            "user_vehicle_model": vehicle_model,
            "user_vehicle_year": vehicle_year,
        },
    )
    print(f"[{env}] call response: {outcome.model_dump()}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent", description="Manage the ElevenLabs voice agent.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create-agent", help="Create a brand-new agent from the definition (from-scratch setup)."
    )
    create_parser.add_argument(
        "--env", required=True, help="Environment to target (e.g. dev, prod)."
    )

    sync_parser = subparsers.add_parser(
        "sync-agent", help="Push the agent definition to an environment."
    )
    sync_parser.add_argument("--env", required=True, help="Environment to target (e.g. dev, prod).")

    call_parser = subparsers.add_parser("call", help="Place one outbound call.")
    call_parser.add_argument("--env", required=True, help="Environment to target (e.g. dev, prod).")
    call_parser.add_argument(
        "--to", required=True, dest="to_number", help="Destination phone number (E.164)."
    )
    call_parser.add_argument("--user-id", required=True, help="Customer record id.")
    call_parser.add_argument("--slot1", required=True, dest="slot_1", help="First proposed slot.")
    call_parser.add_argument("--slot2", required=True, dest="slot_2", help="Second proposed slot.")
    call_parser.add_argument(
        "--make", required=True, dest="vehicle_make", help="Customer vehicle make."
    )
    call_parser.add_argument(
        "--model", required=True, dest="vehicle_model", help="Customer vehicle model."
    )
    call_parser.add_argument(
        "--year", required=True, dest="vehicle_year", help="Customer vehicle model year."
    )

    args = parser.parse_args()

    if args.command == "create-agent":
        _create_agent(args.env)
    elif args.command == "sync-agent":
        _sync_agent(args.env)
    elif args.command == "call":
        _call(
            env=args.env,
            to_number=args.to_number,
            user_id=args.user_id,
            slot_1=args.slot_1,
            slot_2=args.slot_2,
            vehicle_make=args.vehicle_make,
            vehicle_model=args.vehicle_model,
            vehicle_year=args.vehicle_year,
        )


if __name__ == "__main__":
    main()
