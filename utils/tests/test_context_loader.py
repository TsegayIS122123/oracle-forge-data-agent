from agent.context_loader import build_context_layers


def test_build_context_layers_for_known_dataset():
    context = build_context_layers(
        dataset="query_bookreview",
        user_question="What is the average rating for english books?",
    )
    assert "MEMORY.md" in context.layer_1_architecture
    assert "Book Reviews" in context.layer_2_domain or "query_bookreview" in context.layer_2_domain
    assert context.system_prompt


def test_build_context_layers_handles_missing_corrections():
    context = build_context_layers(
        dataset="query_yelp",
        user_question="Top cities by rating?",
    )
    assert context.layer_3_corrections
