async def a():
    asyncio.sleep(1)
    return 5


def main():
    print("Test")
    print(await a)
    print("Test")


main()
