import os
import toml
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger

from .translations import t


CUSTOM_CONFIG_DIR = os.path.join("outputs", "user_proj", "custom_configs")


def ensure_custom_config_dir():
    """Ensure custom config directory exists"""
    if not os.path.exists(CUSTOM_CONFIG_DIR):
        os.makedirs(CUSTOM_CONFIG_DIR, exist_ok=True)


def load_template_config(template_type: str = "minimal") -> Dict[str, Any]:
    """Load template config file"""
    if template_type == "minimal":
        template_path = "config.minimal.toml"
    elif template_type == "full":
        template_path = "config.full-example.toml"
    else:
        raise ValueError(f"Unknown template type: {template_type}")
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template config not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return toml.load(f)


def get_user_custom_configs(user_email: str) -> List[Dict[str, Any]]:
    """Get list of user's custom configs"""
    ensure_custom_config_dir()
    
    configs = []
    email_safe = user_email.replace("@", "_").replace(".", "_")
    user_dir = os.path.join(CUSTOM_CONFIG_DIR, email_safe)
    
    if not os.path.exists(user_dir):
        return configs
    
    for filename in os.listdir(user_dir):
        if filename.endswith(".toml"):
            config_path = os.path.join(user_dir, filename)
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = toml.load(f)
                
                config_name = filename[:-5]
                configs.append({
                    "name": config_name,
                    "path": config_path,
                    "created_at": datetime.fromtimestamp(os.path.getctime(config_path)).isoformat(),
                    "updated_at": datetime.fromtimestamp(os.path.getmtime(config_path)).isoformat(),
                    "language": config_data.get("llm", {}).get("language", "chs")
                })
            except Exception as e:
                logger.warning(f"Failed to load config {config_path}: {e}")
                continue
    
    return sorted(configs, key=lambda x: x["updated_at"], reverse=True)


def save_custom_config(user_email: str, config_name: str, config_data: Dict[str, Any]) -> str:
    """Save custom config to file"""
    ensure_custom_config_dir()
    
    email_safe = user_email.replace("@", "_").replace(".", "_")
    user_dir = os.path.join(CUSTOM_CONFIG_DIR, email_safe)
    
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    
    config_filename = f"{config_name}.toml"
    config_path = os.path.join(user_dir, config_filename)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        toml.dump(config_data, f)
    
    logger.info(f"Saved custom config for user {user_email}: {config_path}")
    return config_path


def load_custom_config(config_path: str) -> Dict[str, Any]:
    """Load custom config from file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return toml.load(f)


def delete_custom_config(config_path: str) -> bool:
    """Delete custom config file"""
    try:
        if os.path.exists(config_path):
            os.remove(config_path)
            logger.info(f"Deleted custom config: {config_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete config {config_path}: {e}")
        return False


def validate_config_name(config_name: str) -> bool:
    """Validate config name"""
    if not config_name:
        return False
    
    if len(config_name) > 50:
        return False
    
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']
    if any(char in config_name for char in invalid_chars):
        return False
    
    return True


def get_config_display_name(config_data: Dict[str, Any]) -> str:
    """Get display name from config data"""
    llm_config = config_data.get("llm", {})
    chat_config = llm_config.get("chat", {})
    
    model = chat_config.get("model", "Unknown")
    language = llm_config.get("language", "chs")
    
    lang_display = "中文" if language == "chs" else "English"
    
    return f"{lang_display} | {model}"


def show_config_dialog(user_manager):
    """Show config management dialog"""
    @st.dialog(t("custom_config"), width="large")
    def config_dialog():
        tab1, tab2 = st.tabs([f"{t('create_config')}", f"{t('manage_and_select_config')}"])

        with tab1:
            st.subheader(f"{t('create_config')}")
            template_type = st.radio(
                f"{t('select_template')}",
                options=["minimal", "full"],
                format_func=lambda x: f"{t('minimal_template') if x == 'minimal' else t('full_template')}",
                horizontal=True
            )

            try:
                template_config = load_template_config(template_type)
                config_display = toml.dumps(template_config)
                edited_config = st.text_area(
                    f"{t('edit_config')}",
                    value=config_display,
                    height=500,
                    help=f"{t('config_help')}"
                )

            except Exception as e:
                st.error(f"Failed to load template: {e}")
                return

            col1, col2 = st.columns([1, 5])
            with col1:
                config_name = st.text_input(f"{t('config_name')}", max_chars=50, placeholder="my-config")
            with col2:
                st.write(f"{t('config_name_placeholder')}")

            set_as_current = st.checkbox(f"{t('set_as_current_config')}", value=True, help=f"{t('set_as_current_config_help')}")

            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button(f"💾 {t('save')}", type="primary"):
                    if not config_name:
                        st.error(f"{t('config_name_required')}")
                    elif not validate_config_name(config_name):
                        st.error(f"{t('config_name_invalid')}")
                    else:
                        try:
                            edited_config_dict = toml.loads(edited_config)
                            config_path = save_custom_config(st.user.email, config_name, edited_config_dict)
                            if set_as_current:
                                user_manager.set_user_custom_config(st.user.email, config_path)
                            st.success(f"{t('config_saved')}: {config_path}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"{t('config_save_error')}: {e}")

        with tab2:
            st.subheader(f"{t('manage_and_select_config')}")

            current_config_path = user_manager.get_user_custom_config(st.user.email)

            if current_config_path:
                try:
                    current_config_data = load_custom_config(current_config_path)
                    st.info(f"{t('current_config')}: **{get_config_display_name(current_config_data)}**")
                except:
                    st.info(f"{t('current_config')}")

            user_configs = get_user_custom_configs(st.user.email)

            if not user_configs:
                st.info(f"{t('no_custom_configs')}")
            else:
                for config_info in user_configs:
                    config_data = load_custom_config(config_info['path'])
                    is_selected = config_info['path'] == current_config_path

                    with st.expander(f"📄 **{config_info['name']}** - {get_config_display_name(config_data)} {'- **✓ ' + t('selected') + "**" if is_selected else ''}", expanded=is_selected):
                        st.caption(f"{t('created_at')}: {config_info['created_at']}")

                        with st.container(horizontal=True):
                            if is_selected:
                                if st.button(f"❌ {t('clear')}", key=f"clear_{config_info['name']}", type="primary"):
                                    if user_manager.clear_user_custom_config(st.user.email):
                                        st.success(f"{t('config_cleared')}")
                                        st.rerun()
                            else:
                                if st.button(f"✓ {t('select')}", key=f"select_{config_info['name']}", type="secondary"):
                                    if user_manager.set_user_custom_config(st.user.email, config_info['path']):
                                        st.success(f"{t('config_selected')}")
                                        st.rerun()

                            if st.button(f"🗑️ {t('delete')}", key=f"delete_{config_info['name']}", type="secondary"):
                                if delete_custom_config(config_info['path']):
                                    user_manager.clear_user_custom_config(st.user.email)
                                    st.success(f"{t('config_deleted')}")
                                    st.rerun()

                        st.code(toml.dumps(config_data), language="toml")

            if current_config_path:
                st.write("---")
                st.write(f"{t('apply_config_note')}")

    config_dialog()
