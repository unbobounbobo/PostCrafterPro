#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update prompts with improved JSON output instructions"""

from app.services.prompt_service import PromptService

def main():
    print('[INFO] Updating prompts with improved JSON instructions...')

    service = PromptService()
    service.reset_to_defaults()

    print('[SUCCESS] Prompts updated!')
    print('  - Added explicit instruction: No code blocks')
    print('  - Added explicit instruction: Raw JSON only')
    print('\n[INFO] Restart the app to apply changes\n')

if __name__ == '__main__':
    main()
