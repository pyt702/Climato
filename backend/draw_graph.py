from graph.graph import app

def generate_image():
    try:
        img_bytes = app.get_graph().draw_mermaid_png()
        with open("graph_flow.png", "wb") as f:
            f.write(img_bytes)
        print("Successfully saved graph architecture to graph_flow.png")
    except Exception as e:
        print(f"Error generating PNG (ensure you have internet access for the mermaid API): {e}")               

if __name__ == "__main__":
    generate_image()
