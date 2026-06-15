"""
Flashcard App - Spaced Repetition Learning System
A professional flashcard application with spaced repetition algorithm
Author: Python Learning Project
"""

import json
import os
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import argparse
import sys

class Flashcard:
    """Represents a single flashcard with spaced repetition data"""
    
    def __init__(self, question: str, answer: str, category: str = "General"):
        self.question = question
        self.answer = answer
        self.category = category
        self.ease_factor = 2.5  # Initial ease factor (2.5 = normal)
        self.interval = 1  # Interval in days
        self.repetitions = 0  # Number of times reviewed
        self.next_review = datetime.now().date()  # When to review next
        self.created_date = datetime.now().date()
        self.last_reviewed = None
        self.mastery_level = 0  # 0-5 mastery level
    
    def to_dict(self) -> Dict:
        """Convert flashcard to dictionary for JSON storage"""
        return {
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'ease_factor': self.ease_factor,
            'interval': self.interval,
            'repetitions': self.repetitions,
            'next_review': self.next_review.isoformat(),
            'created_date': self.created_date.isoformat(),
            'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None,
            'mastery_level': self.mastery_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Flashcard':
        """Create flashcard from dictionary"""
        card = cls(data['question'], data['answer'], data['category'])
        card.ease_factor = data['ease_factor']
        card.interval = data['interval']
        card.repetitions = data['repetitions']
        card.next_review = datetime.fromisoformat(data['next_review']).date()
        card.created_date = datetime.fromisoformat(data['created_date']).date()
        if data['last_reviewed']:
            card.last_reviewed = datetime.fromisoformat(data['last_reviewed']).date()
        card.mastery_level = data['mastery_level']
        return card
    
    def review(self, quality: int) -> None:
        """
        Update card based on review quality (0-5)
        0: Blackout (completely forgot)
        1: Incorrect (wrong answer)
        2: Hard (correct but difficult)
        3: Good (correct with effort)
        4: Easy (correct easily)
        5: Perfect (knew immediately)
        """
        self.last_reviewed = datetime.now().date()
        self.repetitions += 1
        
        if quality >= 3:  # Correct answer
            # SM-2 algorithm for spaced repetition
            if self.repetitions == 1:
                self.interval = 1
            elif self.repetitions == 2:
                self.interval = 6
            else:
                self.interval = round(self.interval * self.ease_factor)
            
            # Update ease factor
            self.ease_factor = self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            
            # Ensure ease factor doesn't go too low
            if self.ease_factor < 1.3:
                self.ease_factor = 1.3
            
            # Update mastery level
            self.mastery_level = min(5, self.mastery_level + 1)
            
        else:  # Incorrect answer
            self.interval = 1
            self.repetitions = 0
            self.mastery_level = max(0, self.mastery_level - 2)
            # Reduce ease factor for wrong answers
            self.ease_factor = max(1.3, self.ease_factor - 0.2)
        
        # Set next review date
        self.next_review = datetime.now().date() + timedelta(days=self.interval)

class FlashcardDeck:
    """Manages a collection of flashcards"""
    
    def __init__(self, name: str = "My Deck"):
        self.name = name
        self.cards: List[Flashcard] = []
        self.categories: set = set()
    
    def add_card(self, card: Flashcard) -> None:
        """Add a flashcard to the deck"""
        self.cards.append(card)
        self.categories.add(card.category)
    
    def remove_card(self, index: int) -> bool:
        """Remove a flashcard by index"""
        if 0 <= index < len(self.cards):
            self.cards.pop(index)
            return True
        return False
    
    def get_cards_for_review(self) -> List[Flashcard]:
        """Get cards that are due for review"""
        today = datetime.now().date()
        return [card for card in self.cards if card.next_review <= today]
    
    def get_statistics(self) -> Dict:
        """Get deck statistics"""
        if not self.cards:
            return {}
        
        today = datetime.now().date()
        due_cards = self.get_cards_for_review()
        
        return {
            'total_cards': len(self.cards),
            'due_cards': len(due_cards),
            'mastered_cards': sum(1 for c in self.cards if c.mastery_level >= 4),
            'learning_cards': sum(1 for c in self.cards if 0 < c.mastery_level < 4),
            'new_cards': sum(1 for c in self.cards if c.repetitions == 0),
            'categories': len(self.categories),
            'average_mastery': sum(c.mastery_level for c in self.cards) / len(self.cards) if self.cards else 0
        }
    
    def search_cards(self, query: str) -> List[Flashcard]:
        """Search cards by question or answer"""
        query = query.lower()
        return [card for card in self.cards 
                if query in card.question.lower() or query in card.answer.lower()]
    
    def get_cards_by_category(self, category: str) -> List[Flashcard]:
        """Get all cards in a specific category"""
        return [card for card in self.cards if card.category == category]

class FlashcardApp:
    """Main application class"""
    
    def __init__(self, data_file: str = "flashcards.json"):
        self.data_file = data_file
        self.deck = FlashcardDeck()
        self.load_data()
    
    def save_data(self) -> None:
        """Save flashcards to JSON file"""
        data = {
            'name': self.deck.name,
            'cards': [card.to_dict() for card in self.deck.cards]
        }
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Data saved to {self.data_file}")
        except Exception as e:
            print(f"❌ Error saving data: {e}")
    
    def load_data(self) -> None:
        """Load flashcards from JSON file"""
        if not os.path.exists(self.data_file):
            print("📚 No existing data found. Starting with empty deck.")
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.deck.name = data.get('name', 'My Deck')
            for card_data in data.get('cards', []):
                card = Flashcard.from_dict(card_data)
                self.deck.cards.append(card)
                self.deck.categories.add(card.category)
            
            print(f"✅ Loaded {len(self.deck.cards)} flashcards")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
    
    def add_new_card(self) -> None:
        """Interactive card creation"""
        print("\n" + "="*60)
        print("➕ ADD NEW FLASHCARD")
        print("="*60)
        
        question = input("\n📝 Question: ").strip()
        if not question:
            print("❌ Question cannot be empty!")
            return
        
        answer = input("💡 Answer: ").strip()
        if not answer:
            print("❌ Answer cannot be empty!")
            return
        
        category = input("📂 Category (default: General): ").strip()
        if not category:
            category = "General"
        
        card = Flashcard(question, answer, category)
        self.deck.add_card(card)
        self.save_data()
        print(f"\n✅ Card added successfully!")
        print(f"   Category: {category}")
        print(f"   Next review: {card.next_review}")
    
    def review_session(self) -> None:
        """Conduct a review session"""
        due_cards = self.deck.get_cards_for_review()
        
        if not due_cards:
            print("\n" + "="*60)
            print("🎉 GREAT JOB!")
            print("="*60)
            print("\nNo cards due for review today!")
            print(f"📊 Total cards: {len(self.deck.cards)}")
            print(f"📈 Mastered: {len([c for c in self.deck.cards if c.mastery_level >= 4])}")
            print("\nCome back tomorrow for more reviews! 📚")
            return
        
        print("\n" + "="*60)
        print(f"📚 REVIEW SESSION - {len(due_cards)} cards due")
        print("="*60)
        print("\nRating guide:")
        print("  0 - Blackout (completely forgot)")
        print("  1 - Incorrect (wrong answer)")
        print("  2 - Hard (correct but difficult)")
        print("  3 - Good (correct with effort)")
        print("  4 - Easy (correct easily)")
        print("  5 - Perfect (knew immediately)")
        print("\n" + "-"*60)
        
        # Shuffle cards for better learning
        random.shuffle(due_cards)
        
        reviewed = 0
        correct = 0
        
        for idx, card in enumerate(due_cards, 1):
            print(f"\n📇 Card {idx}/{len(due_cards)}")
            print(f"📂 Category: {card.category}")
            print(f"📊 Mastery: {'⭐' * card.mastery_level}{'☆' * (5 - card.mastery_level)}")
            print(f"\n❓ Question: {card.question}")
            
            input("\nPress Enter to reveal answer...")
            print(f"\n✅ Answer: {card.answer}")
            
            while True:
                try:
                    quality = int(input("\n📊 How did you do? (0-5): "))
                    if 0 <= quality <= 5:
                        break
                    print("❌ Please enter a number between 0 and 5")
                except ValueError:
                    print("❌ Invalid input. Please enter 0-5")
            
            card.review(quality)
            reviewed += 1
            if quality >= 3:
                correct += 1
            
            # Show feedback
            if quality >= 3:
                print(f"✅ Great! Next review in {card.interval} days")
            else:
                print(f"🔄 Keep practicing! Review again tomorrow")
        
        # Session summary
        print("\n" + "="*60)
        print("📊 SESSION SUMMARY")
        print("="*60)
        print(f"✅ Cards reviewed: {reviewed}")
        print(f"🎯 Correct: {correct}")
        print(f"📈 Accuracy: {correct/reviewed*100:.1f}%")
        print(f"💪 Improvement: {correct - (reviewed - correct)} points")
        
        self.save_data()
    
    def browse_cards(self) -> None:
        """Browse and manage all cards"""
        if not self.deck.cards:
            print("\n📭 No flashcards found. Add some cards first!")
            return
        
        print("\n" + "="*60)
        print("📖 BROWSE FLASHCARDS")
        print("="*60)
        
        # Show filters
        print("\nFilter options:")
        print("  1. All cards")
        print("  2. By category")
        print("  3. Due for review")
        print("  4. Mastered cards")
        print("  5. New cards")
        print("  6. Search")
        
        choice = input("\nChoose filter (1-6): ").strip()
        
        cards_to_show = []
        if choice == '1':
            cards_to_show = self.deck.cards
        elif choice == '2':
            print(f"\nCategories: {', '.join(sorted(self.deck.categories))}")
            cat = input("Enter category: ").strip()
            cards_to_show = self.deck.get_cards_by_category(cat)
        elif choice == '3':
            cards_to_show = self.deck.get_cards_for_review()
        elif choice == '4':
            cards_to_show = [c for c in self.deck.cards if c.mastery_level >= 4]
        elif choice == '5':
            cards_to_show = [c for c in self.deck.cards if c.repetitions == 0]
        elif choice == '6':
            query = input("Search term: ").strip()
            cards_to_show = self.deck.search_cards(query)
        else:
            cards_to_show = self.deck.cards
        
        if not cards_to_show:
            print("\n📭 No cards match your filter")
            return
        
        print(f"\n{'#'*60}")
        for idx, card in enumerate(cards_to_show, 1):
            print(f"\n{idx}. ❓ {card.question}")
            print(f"   💡 Answer: {card.answer}")
            print(f"   📂 Category: {card.category}")
            print(f"   📊 Mastery: {'⭐' * card.mastery_level}")
            print(f"   📅 Next review: {card.next_review}")
            print(f"   🔄 Times reviewed: {card.repetitions}")
            print("-" * 40)
        
        # Option to delete cards
        delete = input("\n🗑️ Delete a card? (enter number or 'no'): ").strip()
        if delete.isdigit():
            idx = int(delete) - 1
            if 0 <= idx < len(cards_to_show):
                card_to_delete = cards_to_show[idx]
                confirm = input(f"Delete '{card_to_delete.question}'? (y/n): ").lower()
                if confirm == 'y':
                    self.deck.cards.remove(card_to_delete)
                    self.save_data()
                    print("✅ Card deleted!")
    
    def show_statistics(self) -> None:
        """Display detailed statistics"""
        stats = self.deck.get_statistics()
        
        if not stats:
            print("\n📭 No cards to show statistics")
            return
        
        print("\n" + "="*60)
        print("📊 DECK STATISTICS")
        print("="*60)
        print(f"\n📚 Deck name: {self.deck.name}")
        print(f"📇 Total cards: {stats['total_cards']}")
        print(f"⏰ Due for review: {stats['due_cards']}")
        print(f"⭐ Mastered cards: {stats['mastered_cards']}")
        print(f"📖 Learning cards: {stats['learning_cards']}")
        print(f"🆕 New cards: {stats['new_cards']}")
        print(f"📂 Categories: {stats['categories']}")
        print(f"📈 Average mastery: {stats['average_mastery']:.1f}/5.0")
        
        # Progress bar for mastery
        mastery_percent = (stats['mastered_cards'] / stats['total_cards']) * 100
        print(f"\n🎯 Overall progress:")
        bar_length = 40
        filled = int(bar_length * mastery_percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"   [{bar}] {mastery_percent:.1f}%")
        
        # Category breakdown
        print("\n📂 Category breakdown:")
        categories = {}
        for card in self.deck.cards:
            categories[card.category] = categories.get(card.category, 0) + 1
        
        for cat, count in sorted(categories.items()):
            percent = (count / stats['total_cards']) * 100
            print(f"   {cat}: {count} cards ({percent:.1f}%)")
    
    def import_from_csv(self, filepath: str) -> None:
        """Import cards from CSV file"""
        import csv
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header if exists
                
                count = 0
                for row in reader:
                    if len(row) >= 2:
                        question = row[0].strip()
                        answer = row[1].strip()
                        category = row[2].strip() if len(row) > 2 else "General"
                        
                        card = Flashcard(question, answer, category)
                        self.deck.add_card(card)
                        count += 1
                
                self.save_data()
                print(f"✅ Imported {count} cards from {filepath}")
        except Exception as e:
            print(f"❌ Error importing: {e}")
    
    def export_to_csv(self, filepath: str) -> None:
        """Export cards to CSV file"""
        import csv
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Question', 'Answer', 'Category', 'Mastery Level'])
                
                for card in self.deck.cards:
                    writer.writerow([card.question, card.answer, card.category, card.mastery_level])
            
            print(f"✅ Exported {len(self.deck.cards)} cards to {filepath}")
        except Exception as e:
            print(f"❌ Error exporting: {e}")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Flashcard App with Spaced Repetition')
    parser.add_argument('--data-file', default='flashcards.json', help='JSON file to store data')
    parser.add_argument('--import-csv', help='Import cards from CSV file')
    parser.add_argument('--export-csv', help='Export cards to CSV file')
    
    args = parser.parse_args()
    
    app = FlashcardApp(args.data_file)
    
    # Handle import/export from command line
    if args.import_csv:
        app.import_from_csv(args.import_csv)
        return
    
    if args.export_csv:
        app.export_to_csv(args.export_csv)
        return
    
    # Interactive menu
    while True:
        print("\n" + "="*60)
        print("🎴 FLASHCARD APP - Spaced Repetition System")
        print("="*60)
        
        # Show quick stats
        stats = app.deck.get_statistics()
        if stats:
            due = stats.get('due_cards', 0)
            if due > 0:
                print(f"⏰ {due} cards waiting for review!")
        
        print("\n📌 MAIN MENU")
        print("="*40)
        print("1. 🔄 Start Review Session")
        print("2. ➕ Add New Flashcard")
        print("3. 📖 Browse All Cards")
        print("4. 📊 View Statistics")
        print("5. 📥 Import Cards (CSV)")
        print("6. 📤 Export Cards (CSV)")
        print("7. 🗑️ Reset All Data")
        print("8. 🚪 Exit")
        print("="*40)
        
        choice = input("\n👉 Enter your choice (1-8): ").strip()
        
        if choice == '1':
            app.review_session()
        elif choice == '2':
            app.add_new_card()
        elif choice == '3':
            app.browse_cards()
        elif choice == '4':
            app.show_statistics()
        elif choice == '5':
            filepath = input("Enter CSV file path: ").strip()
            app.import_from_csv(filepath)
        elif choice == '6':
            filepath = input("Enter CSV file path to save: ").strip()
            app.export_to_csv(filepath)
        elif choice == '7':
            confirm = input("⚠️ Delete ALL cards? (yes/no): ").lower()
            if confirm == 'yes':
                app.deck = FlashcardDeck()
                app.save_data()
                print("✅ All data deleted!")
        elif choice == '8':
            print("\n👋 Thanks for using Flashcard App! Keep learning! 📚")
            break
        else:
            print("❌ Invalid choice. Please enter 1-8")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Happy learning!")
        sys.exit(0)