def combine(facial=None, lipsync=None, audio=None, metadata=None, visual=None):
    """
    Combines individual analysis scores into a final verdict using specific weights.
    
    Weights:
    - Facial: 30% 
    - LipSync: 30%
    - Audio: 20%
    - Metadata: 20%
    """
    
    # Handle 'visual' (pixel artifacts) if passed instead of or alongside facial
    if facial is None and visual is not None:
        facial = visual
    elif facial is not None and visual is not None:
        # Take the stronger of the two signals for facial analysis
        facial = max(facial, visual)

    # Apply Base Weights
    weights = {
        "facial": 0.30,
        "lipsync": 0.30,
        "audio": 0.20,
        "metadata": 0.20
    }
    
    total_weight = 0.0
    weighted_score = 0.0

    if facial is not None:
        weighted_score += facial * weights["facial"]
        total_weight += weights["facial"]

    if lipsync is not None:
        weighted_score += lipsync * weights["lipsync"]
        total_weight += weights["lipsync"]

    if audio is not None:
        weighted_score += audio * weights["audio"]
        total_weight += weights["audio"]

    if metadata is not None:
        weighted_score += metadata * weights["metadata"]
        total_weight += weights["metadata"]

    if total_weight == 0:
        return 0.0

    # Normalize the score (e.g., if Audio is missing, it dynamically re-distributes)
    final_score = weighted_score / total_weight
    
    # Ensure final_score falls strictly between 0 and 1
    final_score = max(0.0, min(1.0, final_score))
    
    return final_score
