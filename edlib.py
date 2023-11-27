# Example Command
# commands = [
#     { 'text': 'Run Crypto Bela Strategy', 'action': CryptoBelaStrategyV2 },
#     { 'text': 'Cancel All Open Orders', 'action': lambda: client.cancel_open_orders('BTCUSDT') },
# ]
def InputLoop(commands):
    commands.append({'text': 'Exit', 'action': ''})
    while True:
        for i in range(len(commands)):
            print(f'{i}: {commands[i]["text"]}')
        choice = int(input('Enter Choice: '))

        
        if choice >= len(commands) - 1:
            print('Goodbye')
            break

        commands[choice]['action']()
        print('Action Completed: ' + commands[choice]['text'])
        
        print('Goodbye')
        break

    