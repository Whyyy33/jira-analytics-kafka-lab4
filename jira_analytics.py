import requests
import pandas as pd
import matplotlib.pyplot as plt
import json
import logging
from datetime import datetime
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JiraAnalytics:
    def __init__(self, config_path="config.json"):
        """Инициализация с загрузкой конфигурации"""
        self.load_config(config_path)
        self.session = requests.Session()
        self.output_dir = "outputs"
        Path(self.output_dir).mkdir(exist_ok=True)
        
    def load_config(self, config_path):
        """Загрузка конфигурации из JSON файла"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.jira_server = config['jira_server']
            self.project_key = config['project_key']
            self.max_results = config.get('max_results', 1000)
            logger.info(f"Конфигурация загружена: проект {self.project_key}")
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            raise
    
    def get_issues(self, jql):
        """Получение задач из JIRA по JQL запросу"""
        all_issues = []
        start_at = 0
        
        while True:
            params = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': self.max_results,
                'fields': 'key,created,updated,status,resolutiondate,assignee,reporter,timespent,priority,changelog',
                'expand': 'changelog'
            }
            
            try:
                response = self.session.get(f"{self.jira_server}/rest/api/2/search", params=params)
                response.raise_for_status()
                data = response.json()
                
                issues = data['issues']
                all_issues.extend(issues)
                logger.info(f"Получено {len(issues)} задач (всего: {len(all_issues)})")
                
                if start_at + len(issues) >= data['total']:
                    break
                start_at += len(issues)
                
            except Exception as e:
                logger.error(f"Ошибка получения задач: {e}")
                break
        
        return all_issues
    
    def prepare_data(self):
        """Подготовка данных для анализа"""
        logger.info("Получение задач для анализа статусов...")
        jql_all_statuses = f'project = {self.project_key}'
        all_status_issues = self.get_issues(jql_all_statuses)
        
        logger.info("Получение закрытых задач для остальных графиков...")
        jql_closed = f'project = {self.project_key} AND status in (Closed, Resolved, Done)'
        closed_issues = self.get_issues(jql_closed)
        
        logger.info("Получение всех задач для графика создания...")
        jql_all = f'project = {self.project_key}'
        all_issues = self.get_issues(jql_all)
        
        return all_status_issues, closed_issues, all_issues
    
    def plot_lead_time_histogram(self, closed_issues):
        """Гистограмма времени в открытом состоянии"""
        if not closed_issues:
            logger.warning("Нет закрытых задач для анализа")
            return
            
        lead_times = []
        for issue in closed_issues:
            fields = issue['fields']
            created = fields.get('created')
            resolved = fields.get('resolutiondate')
            
            if created and resolved:
                created_dt = pd.to_datetime(created)
                resolved_dt = pd.to_datetime(resolved)
                lead_time_days = (resolved_dt - created_dt).total_seconds() / (24 * 3600)
                lead_times.append(lead_time_days)
        
        if not lead_times:
            logger.warning("Нет данных для гистограммы времени выполнения")
            return
            
        plt.figure(figsize=(12, 6))
        plt.hist(lead_times, bins=30, alpha=0.7, edgecolor='black')
        plt.xlabel('Время выполнения (дни)')
        plt.ylabel('Количество задач')
        plt.title(f'Гистограмма времени выполнения задач (KAFKA)\nВсего задач: {len(lead_times)}')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/01_lead_time_histogram.png', dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("Гистограмма времени выполнения сохранена")
    
    def plot_time_in_status(self, all_status_issues):
        """Диаграммы распределения времени по состояниям задачи"""
        if not all_status_issues:
            logger.warning("Нет задач для анализа времени в статусах")
            return
            
        status_stats = {}
        
        for issue in all_status_issues:
            fields = issue['fields']
            status = fields.get('status', {}).get('name', 'Неизвестно')
            created = fields.get('created')
            updated = fields.get('updated')
            
            if not created or not updated:
                continue
                
            created_dt = pd.to_datetime(created)
            updated_dt = pd.to_datetime(updated)
            
            # Время от создания до последнего обновления в этом статусе
            time_in_status_days = (updated_dt - created_dt).total_seconds() / (24 * 3600)
            
            if status not in status_stats:
                status_stats[status] = []
            status_stats[status].append(time_in_status_days)
        
        if not status_stats:
            logger.warning("Нет данных для анализа времени по статусам")
            return
        
        graphs_created = 0
        for status, times in status_stats.items():
            if len(times) < 2:
                continue
                
            try:
                plt.figure(figsize=(10, 6))
                plt.hist(times, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
                plt.xlabel('Время в статусе (дни)')
                plt.ylabel('Количество задач')
                plt.title(f'Распределение времени для статуса: {status}\nЗадач: {len(times)}')
                plt.grid(True, alpha=0.3)
                
                safe_status = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in str(status)).rstrip()
                filename = f'{self.output_dir}/02_time_in_status_{safe_status}.png'
                
                plt.tight_layout()
                plt.savefig(filename, dpi=150, bbox_inches='tight')
                plt.close()
                
                graphs_created += 1
                logger.info(f"Создана диаграмма для статуса: {status} ({len(times)} задач)")
                
            except Exception as e:
                logger.error(f"Ошибка создания графика для статуса {status}: {e}")
                continue
        
        logger.info(f"Создано {graphs_created} диаграмм распределения времени по статусам")
    
    def plot_daily_issue_flow(self, all_issues):
        """График создания и закрытия задач по дням"""
        if not all_issues:
            return
            
        created_dates = []
        resolved_dates = []
        
        for issue in all_issues:
            fields = issue['fields']
            created = fields.get('created')
            resolved = fields.get('resolutiondate')
            
            if created:
                created_dates.append(pd.to_datetime(created).date())
            if resolved:
                resolved_dates.append(pd.to_datetime(resolved).date())
        
        all_dates = created_dates + resolved_dates
        if not all_dates:
            return
            
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        date_range = pd.date_range(start=min_date, end=max_date, freq='D')
        
        daily_data = []
        for date in date_range:
            date_str = date.date()
            created_count = created_dates.count(date_str)
            resolved_count = resolved_dates.count(date_str)
            daily_data.append({
                'date': date,
                'created': created_count,
                'resolved': resolved_count
            })
        
        df = pd.DataFrame(daily_data)
        df['created_cumulative'] = df['created'].cumsum()
        df['resolved_cumulative'] = df['resolved'].cumsum()
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        ax1.plot(df['date'], df['created'], label='Создано', linewidth=2)
        ax1.plot(df['date'], df['resolved'], label='Закрыто', linewidth=2)
        ax1.set_title('Ежедневное количество созданных и закрытых задач')
        ax1.set_ylabel('Количество задач')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(df['date'], df['created_cumulative'], label='Всего создано', linewidth=2)
        ax2.plot(df['date'], df['resolved_cumulative'], label='Всего закрыто', linewidth=2)
        ax2.set_title('Накопительный итог задач')
        ax2.set_xlabel('Дата')
        ax2.set_ylabel('Количество задач')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/03_daily_issue_flow.png', dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("График ежедневного потока задач сохранен")
    
    def plot_top_users(self, closed_issues):
        """Топ 30 пользователей по количеству задач"""
        if not closed_issues:
            return
            
        user_stats = {}
        
        for issue in closed_issues:
            fields = issue['fields']
            
            assignee_data = fields.get('assignee')
            if assignee_data and isinstance(assignee_data, dict):
                assignee = assignee_data.get('displayName', 'Не назначен')
            else:
                assignee = 'Не назначен'
                
            reporter_data = fields.get('reporter')
            if reporter_data and isinstance(reporter_data, dict):
                reporter = reporter_data.get('displayName', 'Неизвестно')
            else:
                reporter = 'Неизвестно'
            
            if assignee not in user_stats:
                user_stats[assignee] = {'assignee': 0, 'reporter': 0}
            user_stats[assignee]['assignee'] += 1
            
            if reporter not in user_stats:
                user_stats[reporter] = {'assignee': 0, 'reporter': 0}
            user_stats[reporter]['reporter'] += 1
        
        user_list = []
        for user, stats in user_stats.items():
            total = stats['assignee'] + stats['reporter']
            user_list.append({
                'user': user,
                'total': total,
                'assignee': stats['assignee'],
                'reporter': stats['reporter']
            })
        
        user_list.sort(key=lambda x: x['total'], reverse=True)
        top_users = user_list[:30]
        
        if not top_users:
            return
            
        users = [u['user'] for u in top_users]
        assignee_counts = [u['assignee'] for u in top_users]
        reporter_counts = [u['reporter'] for u in top_users]
        
        plt.figure(figsize=(12, 10))
        y_pos = range(len(users))
        
        plt.barh(y_pos, assignee_counts, alpha=0.7, label='Исполнитель', color='blue')
        plt.barh(y_pos, reporter_counts, left=assignee_counts, alpha=0.7, label='Репортер', color='orange')
        
        plt.ylabel('Пользователь')
        plt.xlabel('Количество задач')
        plt.title('Топ 30 пользователей по количеству задач\n(Исполнитель + Репортер)')
        plt.yticks(y_pos, users)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/04_top_users.png', dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("График топ пользователей сохранен")
    
    def plot_user_worklog_histogram(self, closed_issues):
        """Гистограмма затраченного времени по пользователям"""
        if not closed_issues:
            return
            
        user_times = {}
        
        for issue in closed_issues:
            fields = issue['fields']
            timespent = fields.get('timespent', 0)
            
            assignee_data = fields.get('assignee')
            if assignee_data and isinstance(assignee_data, dict):
                assignee = assignee_data.get('displayName', 'Не назначен')
            else:
                assignee = 'Не назначен'
            
            if timespent and timespent > 0:
                time_hours = timespent / 3600
                
                if assignee not in user_times:
                    user_times[assignee] = []
                user_times[assignee].append(time_hours)
        
        all_times = []
        for times in user_times.values():
            all_times.extend(times)
        
        if not all_times:
            logger.warning("Нет данных о затраченном времени")
            return
            
        plt.figure(figsize=(12, 6))
        plt.hist(all_times, bins=30, alpha=0.7, edgecolor='black')
        plt.xlabel('Затраченное время (часы)')
        plt.ylabel('Количество задач')
        plt.title('Распределение затраченного времени на задачи')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/05_user_worklog_histogram.png', dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("Гистограмма затраченного времени сохранена")
    
    def plot_issues_by_priority(self, closed_issues):
        """Количество задач по приоритетам"""
        if not closed_issues:
            return
            
        priority_count = {}
        
        for issue in closed_issues:
            fields = issue['fields']
            priority = fields.get('priority', {}).get('name', 'Не установлен')
            
            if priority not in priority_count:
                priority_count[priority] = 0
            priority_count[priority] += 1
        
        sorted_priorities = sorted(priority_count.items(), key=lambda x: x[1], reverse=True)
        
        priorities = [p[0] for p in sorted_priorities]
        counts = [p[1] for p in sorted_priorities]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(priorities, counts, alpha=0.7, edgecolor='black')
        
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(count), ha='center', va='bottom')
        
        plt.xlabel('Приоритет')
        plt.ylabel('Количество задач')
        plt.title('Распределение задач по приоритетам')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/06_issues_by_priority.png', dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("График по приоритетам сохранен")
    
    def generate_all_reports(self):
        """Генерация всех отчетов"""
        try:
            logger.info("Начало генерации отчетов для проекта KAFKA")
            
            all_status_issues, closed_issues, all_issues = self.prepare_data()
            
            if not all_status_issues:
                logger.error("Не найдено задач для анализа")
                return
            
            self.plot_lead_time_histogram(closed_issues)
            self.plot_time_in_status(all_status_issues)
            self.plot_daily_issue_flow(all_issues)
            self.plot_top_users(closed_issues)
            self.plot_user_worklog_histogram(closed_issues)
            self.plot_issues_by_priority(closed_issues)
            
            logger.info("Все отчеты успешно сгенерированы в папке 'outputs'")
            
        except Exception as e:
            logger.error(f"Ошибка при генерации отчетов: {e}")

def main():
    """Основная функция запуска"""
    analytics = JiraAnalytics()
    analytics.generate_all_reports()

if __name__ == "__main__":
    main()