def combine(facial=None, lipsync=None, audio=None, metadata=None, visual=None):
    """
    Combines individual analysis scores into a final verdict using specific weights.
    
    Weights:
    - Facial: 30% (Also covers core Visual/Image artifacts if passed here)
    - LipSync: 30%
    - Audio: 20%
    - Metadata: 20%
    """
    
    # 1. Identify maximum risk across all components (Veto Logic)
    max_risk = 0.0
    if facial is not None: max_risk = max(max_risk, facial)
    if visual is not None: max_risk = max(max_risk, visual) # Legacy image model artifacts
    if lipsync is not None: max_risk = max(max_risk, lipsync)
    if audio is not None: max_risk = max(max_risk, audio)
    if metadata is not None: max_risk = max(max_risk, metadata * 0.9) 

    # If any core detection (Visual/Facial/Lipsync) is sufficiently high (> 0.55), 
    # we trust the AI and immediately veto to avoid dilution by 'normal' metadata.
    # A single manipulated component makes the whole media fake!
    if max_risk > 0.55:
        return max_risk

    # 2. Weighted Fusion
    # Default Base Weights
    weights = {
        "facial": 0.30,
        "lipsync": 0.30,
        "audio": 0.20,
        "metadata": 0.20
    }
    
    # Handle 'visual' (pixel artifacts) as part of 'facial' logic or additive?
    # Strategy: If both 'visual' and 'facial' are present, we fuse them into a single 'facial' score.
    # If only 'visual' is present (Image upload), it becomes the 'facial' score.
    
    if facial is None and visual is not None:
        facial = visual
    elif facial is not None and visual is not None:
        # Take the stronger of the two signals for facial analysis
        facial = max(facial, visual)

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

    # Normalize the score (e.g. if Audio is missing, re-distribute weights among others)
    final_score = weighted_score / total_weight
    
    return final_score
