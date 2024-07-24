import argparse
from collection import Collection

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ScoresManager", description="Manage the collection of scores"
    )

    parser.add_argument(
        "action",
        type=str,
        help="Action to take",
        choices=["export", "clear"],
    )
    parser.add_argument(
        "-c",
        "--collection",
        action="append",
        required=True,
        help="Collection, specified by its directory name",
    )
    parser.add_argument(
        "-r",
        "--refresh",
        action="store_true",
        default=False,
        help="Refresh the export? Defaults to false",
    )
    parser.add_argument(
        "-e", "--export", action="append", help="Type of export or extension"
    )

    # input = "export -c bach_cpe".split()
    args = parser.parse_args()

    if args.action == "export":
        for collection_name in args.collection:
            collection = Collection(collection_name)
            opts = dict(refresh=args.refresh)
            if args.export is not None:
                opts["export_types"] = args.export
            collection.export(**opts)

    elif args.action == "clear":
        for collection_name in args.collection:
            collection = Collection(collection_name)
            if args.export is not None:
                for export_type in args.export:
                    collection.clear_export(export_type)
            else:
                collection.clear_all_exports()
