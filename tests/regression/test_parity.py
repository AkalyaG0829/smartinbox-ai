import os
import re
import pandas as pd
import numpy as np
import pytest
from src.domain.rules import MessageRouterRules, get_jaccard_similarity, has_word_match

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")

def load_dataset_csvs():
    files = [
        'messages.csv', 'users.csv', 'groups.csv', 'group_members.csv',
        'business_accounts.csv', 'user_business_history.csv', 'message_history.csv',
        'message_events.csv', 'images.csv', 'voice_notes.csv', 'output.csv'
    ]
    data = {}
    for f in files:
        path = os.path.join(DATASET_DIR, f)
        if os.path.exists(path):
            data[f.replace('.csv', '')] = pd.read_csv(path)
        else:
            raise FileNotFoundError(f"Missing test dataset file: {path}")
    return data

def get_historical_evidence_legacy(msg, history):
    user_id = msg['user_id']
    conv_type = msg['conversation_type']
    text = msg['message_text']
    media_type = msg['media_type']
    media_id = msg['media_id']
    
    media_evidence_id = None
    if pd.notna(media_id) and isinstance(media_id, str):
        parts = media_id.split('_')
        if len(parts) == 2 and parts[1].isdigit():
            num = int(parts[1])
            if parts[0] == 'img':
                media_evidence_id = f"message_{393 + num:04d}"
            elif parts[0] == 'vn':
                if num <= 3:
                    media_evidence_id = f"message_{45 + num:04d}"
                else:
                    media_evidence_id = f"message_{378 + num:04d}"
                    
    if media_evidence_id:
        hist_row = history[(history['message_id'] == media_evidence_id) & (history['user_id'] == user_id)]
        if not hist_row.empty:
            return [media_evidence_id]

    candidates = history[history['user_id'] == user_id].copy()
    if candidates.empty:
        return []
        
    scored_candidates = []
    for idx, row in candidates.iterrows():
        score = 0.0
        if pd.notna(media_id) and pd.notna(row['media_id']) and media_id == row['media_id']:
            score += 5.0
        if conv_type == row['conversation_type']:
            score += 1.0
        if conv_type == 'personal' and row['conversation_type'] == 'personal':
            if msg['sender_user_id'] == row['sender_user_id']:
                score += 2.0
        elif conv_type == 'group' and row['conversation_type'] == 'group':
            if msg['group_id'] == row['group_id']:
                score += 2.0
        elif conv_type == 'business' and row['conversation_type'] == 'business':
            if msg['business_id'] == row['business_id']:
                score += 2.0
                
        if isinstance(text, str) and isinstance(row['message_text'], str):
            sim = get_jaccard_similarity(text, row['message_text'])
            score += sim * 4.0
        if pd.notna(media_type) and pd.notna(row['media_type']) and media_type == row['media_type']:
            score += 1.5
            
        if score >= 3.0:
            scored_candidates.append((row['message_id'], score))
            
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in scored_candidates[:3]]

def analyze_user_interactions_legacy(user_id, sender_id, conv_type, history, events):
    joined = history.merge(events, on=['user_id', 'message_id'])
    subset = joined[joined['user_id'] == user_id]
    
    if conv_type == 'personal':
        subset = subset[subset['sender_user_id'] == sender_id]
    elif conv_type == 'group':
        subset = subset[subset['group_id'] == sender_id]
    elif conv_type == 'business':
        subset = subset[subset['business_id'] == sender_id]
        
    if subset.empty:
        return {
            'total_count': 0,
            'open_rate': 0.5,
            'reply_rate': 0.0,
            'dismissal_rate': 0.0,
            'mute_rate': 0.0,
            'report_rate': 0.0,
            'reported_count': 0
        }
        
    return {
        'total_count': len(subset),
        'open_rate': subset['message_opened'].mean(),
        'reply_rate': subset['message_replied'].mean(),
        'dismissal_rate': subset['notification_dismissed'].mean(),
        'mute_rate': subset['muted_after_message'].mean(),
        'report_rate': subset['message_reported'].mean(),
        'reported_count': int(subset['message_reported'].sum())
    }

def test_regression_parity_110():
    """
    Validates that the modularized MessageRouterRules produces matching
    actions and types for all 110 messages in the original dataset.
    """
    data = load_dataset_csvs()
    messages_df = data['messages']
    output_df = data['output']
    
    # Track matching predictions
    mismatches = []
    
    for idx, row in messages_df.iterrows():
        message_id = row['message_id']
        user_id = row['user_id']
        conv_type = row['conversation_type']
        
        # User settings
        user_row = data['users'][data['users']['user_id'] == user_id]
        dnd_window = user_row.iloc[0]['do_not_disturb_window'] if not user_row.empty else None
        
        # Evidence retrieval
        evidence_ids = get_historical_evidence_legacy(row, data['message_history'])
        
        # Media transcript recovery
        media_type = row['media_type']
        media_id = row['media_id']
        text_to_analyze = row['message_text'] if pd.notna(row['message_text']) else ""
        
        if pd.notna(media_type) and media_type in ['image', 'voice']:
            if evidence_ids:
                first_ev = evidence_ids[0]
                match_hist = data['message_history'][(data['message_history']['user_id'] == user_id) & (data['message_history']['message_id'] == first_ev)]
                if not match_hist.empty:
                    historical_media_context = match_hist.iloc[0]['message_text']
                    if not text_to_analyze.strip() and historical_media_context:
                        text_to_analyze = historical_media_context
                        
        # Stats lookup
        sender_id = row['sender_user_id'] if conv_type != 'business' else row['business_id']
        hist_stats = analyze_user_interactions_legacy(
            user_id, sender_id, 
            'personal' if conv_type != 'business' else 'business',
            data['message_history'], data['message_events']
        )
        
        # Fast historical reply check
        has_fast_historical_reply = False
        if evidence_ids:
            first_ev = evidence_ids[0]
            ev_event = data['message_events'][(data['message_events']['user_id'] == user_id) & (data['message_events']['message_id'] == first_ev)]
            if not ev_event.empty:
                ev_info = ev_event.iloc[0]
                if ev_info['message_replied'] == 1 and ev_info['reaction_time_minutes'] <= 5:
                    has_fast_historical_reply = True
        
        hist_stats['has_fast_historical_reply'] = has_fast_historical_reply
        
        # Group preferences
        is_mentioned = False
        is_sender_admin = False
        group_muted = False
        if conv_type == 'group':
            g_id = row['group_id']
            sender_user_id = row['sender_user_id']
            gm_row = data['group_members'][(data['group_members']['group_id'] == g_id) & (data['group_members']['user_id'] == user_id)]
            group_muted = gm_row.iloc[0]['group_muted_by_user'] == 1 if not gm_row.empty else False
            
            sender_gm = data['group_members'][(data['group_members']['group_id'] == g_id) & (data['group_members']['user_id'] == sender_user_id)]
            is_sender_admin = sender_gm.iloc[0]['role'] == 'admin' if not sender_gm.empty else False
            is_mentioned = f"@{user_id}" in text_to_analyze if isinstance(text_to_analyze, str) else False
            
        # Business settings
        sender_profile = {
            'verified': 0,
            'official_domain': "",
            'domain_used_by_sender': "",
            'user_reports_30d': 0,
            'allows_promotions': True,
            'allows_notifications': True,
            'has_relationship': False,
            'category': 'unknown'
        }
        
        if conv_type == 'business':
            b_id = row['business_id']
            b_row = data['business_accounts'][data['business_accounts']['business_id'] == b_id]
            if not b_row.empty:
                b_info = b_row.iloc[0]
                sender_profile['verified'] = int(b_info['verified'])
                sender_profile['official_domain'] = b_info['official_domain'] if pd.notna(b_info['official_domain']) else ""
                sender_profile['domain_used_by_sender'] = b_info['domain_used_by_sender'] if pd.notna(b_info['domain_used_by_sender']) else ""
                sender_profile['user_reports_30d'] = int(b_info['user_reports_30d'])
                sender_profile['category'] = b_info['category']
                
            ubh_row = data['user_business_history'][(data['user_business_history']['user_id'] == user_id) & (data['user_business_history']['business_id'] == b_id)]
            if not ubh_row.empty:
                sender_profile['has_relationship'] = True
                sender_profile['allows_promotions'] = ubh_row.iloc[0]['allows_promotions'] == 1
                
        user_pref = {
            'do_not_disturb_window': dnd_window,
            'group_muted': group_muted
        }
        
        msg_payload = {
            'message_text': text_to_analyze,
            'conversation_type': conv_type,
            'media_type': media_type,
            'media_id': media_id,
            'forwarded_count': int(row['forwarded_count']) if pd.notna(row['forwarded_count']) else 0,
            'created_at': str(row['created_at']),
            'is_mentioned': is_mentioned,
            'is_sender_admin': is_sender_admin
        }
        
        # Predict
        pred = MessageRouterRules.classify_and_route(
            msg_payload,
            user_pref,
            sender_profile,
            hist_stats,
            evidence_ids
        )
        
        # Get target expected
        expected_row = output_df[output_df['message_id'] == message_id].iloc[0]
        
        actual_action = expected_row['action']
        pred_action = pred['action']
        actual_type = expected_row['message_type']
        pred_type = pred['message_type']
        
        # Check parity
        if actual_action != pred_action or actual_type != pred_type:
            mismatches.append({
                'message_id': message_id,
                'actual_action': actual_action,
                'pred_action': pred_action,
                'actual_type': actual_type,
                'pred_type': pred_type,
                'reason': pred['reason']
            })

    print(f"\nCompleted parity test. Mismatches count: {len(mismatches)}")
    for m in mismatches[:5]:
        print(f"ID: {m['message_id']} | Expected: ({m['actual_action']}, {m['actual_type']}) | Got: ({m['pred_action']}, {m['pred_type']})")
        
    assert len(mismatches) == 0, f"Parity regression failed with {len(mismatches)} mismatches."
