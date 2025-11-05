from tool import RealtimeTextReplacer

def run_tool():
    """Run the text replacement tool."""
    replacer = RealtimeTextReplacer()
    replacer.start_monitoring()

if __name__ == "__main__":
    run_tool()