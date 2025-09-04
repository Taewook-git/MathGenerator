search_stack() {
    GEMINI_API_KEY="AIzaSyA2gX-s2K48xy82336Ix_V6FmlQ42UeL78" gemini -p "Stack Overflow: $1 - most voted"
}

search_github() {
    GEMINI_API_KEY="AIzaSyA2gX-s2K48xy82336Ix_V6FmlQ42UeL78" gemini -p "GitHub: $1 high stars active"
}
