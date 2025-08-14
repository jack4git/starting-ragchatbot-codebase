import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# Create figure and axis
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis("off")

# Define colors
frontend_color = "#4A90E2"
backend_color = "#7ED321"
ai_color = "#F5A623"
db_color = "#BD10E0"
flow_color = "#333333"


# Helper function to create rounded rectangles
def create_box(ax, x, y, width, height, text, color, text_color="white", fontsize=10):
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.1",
        facecolor=color,
        edgecolor="black",
        linewidth=1.5,
    )
    ax.add_patch(box)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=text_color,
        weight="bold",
        wrap=True,
    )


# Helper function to create arrows
def create_arrow(ax, start_x, start_y, end_x, end_y, text="", offset=0.2):
    arrow = patches.FancyArrowPatch(
        (start_x, start_y),
        (end_x, end_y),
        connectionstyle="arc3,rad=0",
        arrowstyle="->",
        mutation_scale=20,
        color=flow_color,
        linewidth=2,
    )
    ax.add_patch(arrow)
    if text:
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2 + offset
        ax.text(
            mid_x,
            mid_y,
            text,
            ha="center",
            va="center",
            fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )


# Title
ax.text(
    5,
    11.5,
    "RAG System Query Flow",
    ha="center",
    va="center",
    fontsize=18,
    weight="bold",
)

# 1. Frontend Layer
create_box(
    ax,
    0.5,
    9.5,
    2,
    1.2,
    "FRONTEND\n(script.js)\n\nUser Input\nChat Interface",
    frontend_color,
)

# 2. API Layer
create_box(
    ax, 4, 9.5, 2, 1.2, "FASTAPI\n(app.py)\n\n/api/query\nEndpoint", backend_color
)

# 3. RAG System
create_box(
    ax, 7.5, 9.5, 2, 1.2, "RAG SYSTEM\n(rag_system.py)\n\nOrchestrator", backend_color
)

# 4. Session Manager
create_box(
    ax,
    0.5,
    7.5,
    1.8,
    1,
    "SESSION\nMANAGER\n\nConversation\nHistory",
    backend_color,
    fontsize=9,
)

# 5. AI Generator
create_box(ax, 4, 7.5, 2, 1, "AI GENERATOR\n(ai_generator.py)\n\nClaude API", ai_color)

# 6. Tool Manager
create_box(
    ax, 7.5, 7.5, 2, 1, "TOOL MANAGER\n(search_tools.py)\n\nSearch Tools", backend_color
)

# 7. Course Search Tool
create_box(ax, 4, 5.5, 2, 1, "COURSE SEARCH\nTOOL\n\nSemantic Search", backend_color)

# 8. Vector Store
create_box(ax, 7.5, 5.5, 2, 1, "VECTOR STORE\n(vector_store.py)\n\nChromaDB", db_color)

# 9. Document Chunks
create_box(ax, 4, 3.5, 2, 1, "DOCUMENT\nCHUNKS\n\nCourse Content", db_color)

# 10. Course Metadata
create_box(ax, 7.5, 3.5, 2, 1, "COURSE\nMETADATA\n\nTitles & Info", db_color)

# Flow arrows with labels
# Main flow down
create_arrow(ax, 2.5, 10, 4, 10, "1. POST /api/query\n{query, session_id}")
create_arrow(ax, 6, 10, 7.5, 10, "2. rag_system.query()")
create_arrow(ax, 8.5, 9.5, 8.5, 8.5, "3. Get conversation\nhistory")
create_arrow(ax, 7.5, 8, 6, 8, "4. generate_response()\nwith tools")
create_arrow(ax, 5, 7.5, 5, 6.5, "5. Claude decides\nto search")
create_arrow(ax, 6, 6, 7.5, 6, "6. execute_tool()\nsearch_course_content")
create_arrow(ax, 8.5, 5.5, 8.5, 4.5, "7. Semantic search\nChromaDB query")

# Return flow up
create_arrow(ax, 7.5, 4, 6, 4, "8. Search results\nwith metadata", -0.3)
create_arrow(ax, 4, 4.5, 4, 5.5, "9. Formatted results\nback to Claude", -0.3)
create_arrow(ax, 4, 6.5, 4, 7.5, "10. Tool results\nto Claude API", -0.3)
create_arrow(ax, 4, 8.5, 2, 8.5, "11. Final AI response\nwith sources", -0.3)
create_arrow(ax, 2, 9.5, 2, 8.5, "12. JSON response\n{answer, sources}", -0.3)

# Side connections
create_arrow(ax, 1.5, 9.5, 1.5, 8.5, "Session\nmanagement")
create_arrow(ax, 8.5, 7.5, 8.5, 6.5, "Tool\nexecution")

# Data flow indicators
ax.text(0.2, 2, "DATA STORAGE:", ha="left", va="center", fontsize=12, weight="bold")
ax.text(0.2, 1.5, "• ChromaDB Collections", ha="left", va="center", fontsize=10)
ax.text(0.2, 1.2, "• Vector Embeddings", ha="left", va="center", fontsize=10)
ax.text(0.2, 0.9, "• Course Metadata", ha="left", va="center", fontsize=10)
ax.text(0.2, 0.6, "• Conversation History", ha="left", va="center", fontsize=10)

# Legend
legend_y = 2
ax.text(
    6, legend_y + 0.5, "COMPONENTS:", ha="left", va="center", fontsize=12, weight="bold"
)
create_box(ax, 6, legend_y, 0.3, 0.2, "", frontend_color)
ax.text(6.4, legend_y + 0.1, "Frontend", ha="left", va="center", fontsize=10)
create_box(ax, 6, legend_y - 0.3, 0.3, 0.2, "", backend_color)
ax.text(6.4, legend_y - 0.2, "Backend", ha="left", va="center", fontsize=10)
create_box(ax, 6, legend_y - 0.6, 0.3, 0.2, "", ai_color)
ax.text(6.4, legend_y - 0.5, "AI/Claude", ha="left", va="center", fontsize=10)
create_box(ax, 6, legend_y - 0.9, 0.3, 0.2, "", db_color)
ax.text(6.4, legend_y - 0.8, "Database", ha="left", va="center", fontsize=10)

plt.tight_layout()
plt.savefig(
    "/Users/jackivers/Projects/learning/claudecode/starting-ragchatbot-codebase/query_flow_diagram.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white",
)
plt.savefig(
    "/Users/jackivers/Projects/learning/claudecode/starting-ragchatbot-codebase/query_flow_diagram.pdf",
    bbox_inches="tight",
    facecolor="white",
)
plt.show()

print("Query flow diagram saved as query_flow_diagram.png and query_flow_diagram.pdf")
