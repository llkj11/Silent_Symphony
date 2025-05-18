# Helper function for presenting numbered choices and getting valid input
def get_numbered_choice(prompt_text, options_list):
    print(prompt_text)
    for i, option in enumerate(options_list):
        print(f"  {i+1}. {option}")
    
    choice_num = -1
    while choice_num < 1 or choice_num > len(options_list):
        try:
            raw_input = input(f"Enter your choice (1-{len(options_list)}): ")
            choice_num = int(raw_input)
            if not (1 <= choice_num <= len(options_list)):
                print(f"Invalid number. Please enter a number between 1 and {len(options_list)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    return options_list[choice_num - 1] 